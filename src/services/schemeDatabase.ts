/**
 * Scheme Database Service
 * Provides access to the SQLite schemes database directly in the browser
 * using sql.js
 */

import initSqlJs, { Database } from 'sql.js';
import { Scheme } from '../types';

let db: Database | null = null;
let initPromise: Promise<void> | null = null;

/**
 * Initialize the SQLite database
 * Loads the schemes.db file from the public directory
 * Uses local WASM file for offline support
 */
export async function initDatabase(): Promise<void> {
  if (initPromise) {
    return initPromise;
  }

  initPromise = (async () => {
    try {
      // Initialize sql.js with local WASM file
      const SQL = await initSqlJs({
        locateFile: (file: string) => `/${file}`
      });

      // Fetch the database file
      const response = await fetch('/schemes.db');
      if (!response.ok) {
        throw new Error(`Failed to load database: ${response.statusText}`);
      }

      const buffer = await response.arrayBuffer();
      db = new SQL.Database(new Uint8Array(buffer));

      console.log('✅ Database initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize database:', error);
      // Reset initPromise to allow retry
      initPromise = null;
      throw error;
    }
  })();

  return initPromise;
}

/**
 * Get the database instance, initializing if necessary
 */
async function getDb(): Promise<Database> {
  if (!db) {
    await initDatabase();
  }
  if (!db) {
    throw new Error('Database not initialized');
  }
  return db;
}

/**
 * Convert database row to Scheme object
 */
function rowToScheme(row: any): Scheme {
  const categories = row.scheme_categories ? JSON.parse(row.scheme_categories) : [];
  const states = row.beneficiary_states ? JSON.parse(row.beneficiary_states) : [];

  return {
    id: row.slug,
    name: row.scheme_name,
    nameHindi: row.scheme_name, // Database doesn't have Hindi, use same for now
    description: row.brief_description || '',
    descriptionHindi: row.brief_description || '', // Use same for now
    category: categories[0] || 'General',
    state: states.length > 0 ? states.join(', ') : 'All India',
    benefits: [row.brief_description || ''], // Database doesn't have detailed benefits
    eligibilityCriteria: {
      // Database doesn't have detailed criteria, provide basic info
    },
    requiredDocuments: [],
    applicationProcess: 'Visit the official website for application details',
    officialUrl: row.url || 'https://www.myscheme.gov.in'
  };
}

/**
 * Search schemes by query with optional filters
 */
export async function searchSchemes(
  query: string = '',
  filters: {
    state?: string;
    category?: string;
    level?: string;
  } = {},
  limit: number = 10
): Promise<Scheme[]> {
  const database = await getDb();

  try {
    let sql = `
      SELECT * FROM schemes
      WHERE 1=1
    `;
    const params: any[] = [];

    // Add search query if provided
    if (query && query.trim()) {
      sql += ` AND (
        scheme_name LIKE ? OR
        brief_description LIKE ? OR
        scheme_categories LIKE ? OR
        tags LIKE ?
      )`;
      const searchPattern = `%${query}%`;
      params.push(searchPattern, searchPattern, searchPattern, searchPattern);
    }

    // Add state filter
    if (filters.state) {
      sql += ` AND beneficiary_states LIKE ?`;
      params.push(`%${filters.state}%`);
    }

    // Add category filter
    if (filters.category) {
      sql += ` AND scheme_categories LIKE ?`;
      params.push(`%${filters.category}%`);
    }

    // Add level filter
    if (filters.level) {
      sql += ` AND level = ?`;
      params.push(filters.level);
    }

    sql += ` LIMIT ?`;
    params.push(limit);

    const stmt = database.prepare(sql);
    stmt.bind(params);

    const schemes: Scheme[] = [];
    while (stmt.step()) {
      const row = stmt.getAsObject();
      schemes.push(rowToScheme(row));
    }
    stmt.free();

    return schemes;
  } catch (error) {
    console.error('Error searching schemes:', error);
    return [];
  }
}

/**
 * Get a single scheme by ID (slug)
 */
export async function getSchemeById(id: string): Promise<Scheme | null> {
  const database = await getDb();

  try {
    const stmt = database.prepare('SELECT * FROM schemes WHERE slug = ? LIMIT 1');
    stmt.bind([id]);

    if (stmt.step()) {
      const row = stmt.getAsObject();
      stmt.free();
      return rowToScheme(row);
    }
    stmt.free();
    return null;
  } catch (error) {
    console.error('Error getting scheme by ID:', error);
    return null;
  }
}

/**
 * Get all unique categories
 */
export async function getAllCategories(): Promise<string[]> {
  const database = await getDb();

  try {
    const stmt = database.prepare('SELECT DISTINCT scheme_categories FROM schemes');
    const categoriesSet = new Set<string>();

    while (stmt.step()) {
      const row = stmt.getAsObject();
      const cats = row.scheme_categories ? JSON.parse(row.scheme_categories as string) : [];
      cats.forEach((cat: string) => categoriesSet.add(cat));
    }
    stmt.free();

    return Array.from(categoriesSet).sort();
  } catch (error) {
    console.error('Error getting categories:', error);
    return [];
  }
}

/**
 * Get all unique states
 */
export async function getAllStates(): Promise<string[]> {
  const database = await getDb();

  try {
    const stmt = database.prepare('SELECT DISTINCT beneficiary_states FROM schemes');
    const statesSet = new Set<string>();

    while (stmt.step()) {
      const row = stmt.getAsObject();
      const states = row.beneficiary_states ? JSON.parse(row.beneficiary_states as string) : [];
      states.forEach((state: string) => statesSet.add(state));
    }
    stmt.free();

    return Array.from(statesSet).sort();
  } catch (error) {
    console.error('Error getting states:', error);
    return [];
  }
}

/**
 * Get database statistics
 */
export async function getDbStats(): Promise<{
  total: number;
  central: number;
  state: number;
}> {
  const database = await getDb();

  try {
    const totalStmt = database.prepare('SELECT COUNT(*) as count FROM schemes');
    totalStmt.step();
    const total = (totalStmt.getAsObject().count as number) || 0;
    totalStmt.free();

    const centralStmt = database.prepare("SELECT COUNT(*) as count FROM schemes WHERE level='Central'");
    centralStmt.step();
    const central = (centralStmt.getAsObject().count as number) || 0;
    centralStmt.free();

    const stateStmt = database.prepare("SELECT COUNT(*) as count FROM schemes WHERE level='State'");
    stateStmt.step();
    const state = (stateStmt.getAsObject().count as number) || 0;
    stateStmt.free();

    return { total, central, state };
  } catch (error) {
    console.error('Error getting DB stats:', error);
    return { total: 0, central: 0, state: 0 };
  }
}

/**
 * Get schemes by category
 */
export async function getSchemesByCategory(category: string, limit: number = 10): Promise<Scheme[]> {
  return searchSchemes('', { category }, limit);
}

/**
 * Get random featured schemes
 */
export async function getFeaturedSchemes(limit: number = 6): Promise<Scheme[]> {
  const database = await getDb();

  try {
    // Get schemes ordered by priority (higher priority first)
    const stmt = database.prepare(`
      SELECT * FROM schemes
      WHERE priority IS NOT NULL
      ORDER BY priority DESC, scheme_name ASC
      LIMIT ?
    `);
    stmt.bind([limit]);

    const schemes: Scheme[] = [];
    while (stmt.step()) {
      const row = stmt.getAsObject();
      schemes.push(rowToScheme(row));
    }
    stmt.free();

    return schemes;
  } catch (error) {
    console.error('Error getting featured schemes:', error);
    return [];
  }
}
