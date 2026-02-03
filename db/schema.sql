PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
  item_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT,
  default_unit TEXT NOT NULL,
  shelf_life_days_default INTEGER
);

CREATE TABLE IF NOT EXISTS images (
  image_id TEXT PRIMARY KEY,
  file_path TEXT NOT NULL,
  uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_batches (
  batch_id TEXT PRIMARY KEY,
  item_id INTEGER,
  item_name_snapshot TEXT NOT NULL,
  quantity REAL NOT NULL,
  unit TEXT NOT NULL,
  purchase_date TEXT,
  expire_date TEXT,
  location TEXT,
  status TEXT NOT NULL,
  source_type TEXT,
  source_ref_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (item_id) REFERENCES items(item_id)
);

CREATE TABLE IF NOT EXISTS inventory_events (
  event_id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  delta_quantity REAL,
  note TEXT,
  actor TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (batch_id) REFERENCES inventory_batches(batch_id)
);

CREATE TABLE IF NOT EXISTS recipes (
  recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  tags TEXT,
  allergens TEXT,
  steps TEXT,
  nutrition_json TEXT
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
  recipe_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  quantity REAL NOT NULL,
  unit TEXT NOT NULL,
  optional INTEGER DEFAULT 0,
  FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
  FOREIGN KEY (item_id) REFERENCES items(item_id)
);

CREATE TABLE IF NOT EXISTS menu_plans (
  menu_id TEXT PRIMARY KEY,
  days INTEGER NOT NULL,
  servings INTEGER NOT NULL,
  constraints_json TEXT,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_plan_items (
  id TEXT PRIMARY KEY,
  menu_id TEXT NOT NULL,
  date TEXT NOT NULL,
  meal_type TEXT NOT NULL,
  recipe_id INTEGER NOT NULL,
  explain_json TEXT,
  nutrition_json TEXT,
  FOREIGN KEY (menu_id) REFERENCES menu_plans(menu_id),
  FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id)
);

CREATE TABLE IF NOT EXISTS shopping_list_items (
  id TEXT PRIMARY KEY,
  menu_id TEXT NOT NULL,
  item_id INTEGER,
  item_name_snapshot TEXT NOT NULL,
  need_qty REAL NOT NULL,
  unit TEXT NOT NULL,
  reason_json TEXT,
  checked INTEGER DEFAULT 0,
  FOREIGN KEY (menu_id) REFERENCES menu_plans(menu_id),
  FOREIGN KEY (item_id) REFERENCES items(item_id)
);

-- Helpful indexes for planning & lookup
CREATE INDEX IF NOT EXISTS idx_inventory_batches_status_expire
  ON inventory_batches(status, expire_date);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe_id
  ON recipe_ingredients(recipe_id);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_item_id
  ON recipe_ingredients(item_id);

