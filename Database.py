import sqlite3
import os
import sys

DB_NAME = "kitchen_recipes.db"

import os
import sys

#v5 προσθήκη στο get_db_path για εύρεση φακέλου .exe ώστε να δουλεύει σωστά και μετά το packaging με pyinstaller
def get_db_path():
    #εύρεση φακέλου .exe
    if getattr(sys, 'frozen', False):
        # Τρέχει ως εκτελέσιμο
        base_path = os.path.dirname(sys.executable)
    else:
        # Τρέχει ως script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, DB_NAME)


def get_connection():
    """Επιστρέφει ένα νέο connection """
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        difficulty TEXT,
        total_duration INTEGER,
        servings INTEGER DEFAULT 4
    )
    ''')

    # Προσθήκη στήλης servings αν δεν υπάρχει (για υπάρχουσες βάσεις)
    try:
        cursor.execute("ALTER TABLE Recipes ADD COLUMN servings INTEGER DEFAULT 4")
    except sqlite3.OperationalError:
        # Η στήλη υπάρχει ήδη
        pass

    cursor.execute('''CREATE TABLE IF NOT EXISTS Steps(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        step_number INTEGER,
        title TEXT,
        instruction TEXT,
        time_hours TEXT,
        time_minutes TEXT,
        FOREIGN KEY (recipe_id) REFERENCES Recipes (id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ingredients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Recipe_Ingredients (
        recipe_id INTEGER,
        ingredient_id INTEGER,
        amount TEXT,
        PRIMARY KEY (recipe_id, ingredient_id),
        FOREIGN KEY (recipe_id) REFERENCES Recipes(id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES Ingredients(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Step_Ingredients (
        step_id INTEGER,
        ingredient_id INTEGER,
        amount TEXT,
        FOREIGN KEY (step_id) REFERENCES Steps(id) ON DELETE CASCADE,
        FOREIGN KEY (ingredient_id) REFERENCES Ingredients(id)
    )
    ''')

    connection.commit()
    connection.close()
    print("Η βάση δεδομένων είναι έτοιμη!")



def save_new_recipe(title, category, difficulty, duration, servings=4):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO Recipes (title, category, difficulty, total_duration, servings)
            VALUES (?,?,?,?,?)
            """, (title , category, difficulty, duration, servings))

        recipe_id = cursor.lastrowid
        connection.commit()
        print(f"Η συνταγή '{title}' αποθηκεύτηκε με ID: {recipe_id}")
        return recipe_id

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την αποθήκευση: {e}")
        return None
    finally:
        connection.close()


def add_ingredient(name):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO Ingredients (name)
            VALUES (?)
        """, (name,))

        cursor.execute("SELECT id FROM Ingredients WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result is None:
            connection.rollback()
            return None

        ingredient_id = result[0]
        connection.commit()
        return ingredient_id

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την προσθήκη υλικού: {e}")
        return None
    finally:
        connection.close()


def add_recipe_ingredient(recipe_id, ingredient_id, amount):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO Recipe_Ingredients (recipe_id, ingredient_id, amount)
            VALUES (?, ?, ?)
        """, (recipe_id, ingredient_id, amount))
        connection.commit()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά τη σύνδεση υλικού με συνταγή: {e}")
    finally:
        connection.close()


def add_recipe_step(recipe_id, step_number, title, instruction, time_hours, time_minutes):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path) 
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO Steps (recipe_id, step_number, title, instruction, time_hours, time_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recipe_id, step_number, title, instruction, str(time_hours), str(time_minutes)))

        connection.commit()
        step_id = cursor.lastrowid
        print(f"Το βήμα {step_number} προστέθηκε επιτυχώς με ID: {step_id}!")
        return step_id

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την προσθήκη βήματος! {e}")
        return None

    finally:
        connection.close()


def add_step_ingredient(step_id, ingredient_id, amount):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO Step_Ingredients (step_id, ingredient_id, amount)
            VALUES (?, ?, ?)
        """, (step_id, ingredient_id, amount))
        connection.commit()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την προσθήκη υλικού στο βήμα: {e}")
    finally:
        connection.close()


def get_step_ingredients(step_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT Ingredients.name, Step_Ingredients.amount, Ingredients.id
            FROM Ingredients
            JOIN Step_Ingredients ON Ingredients.id = Step_Ingredients.ingredient_id
            WHERE Step_Ingredients.step_id = ?
        """, (step_id,))
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση υλικών βήματος: {e}")
        return []
    finally:
        connection.close()


def find_recipes(search_term):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT * FROM Recipes
            WHERE LOWER(title) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?)
        """, (f"%{search_term}%", f"%{search_term}%"))

        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την αναζήτηση: {e}")
        return []
    finally:
        connection.close()


def get_all_recipes():
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM Recipes ORDER BY title ASC")
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση συνταγών: {e}")
        return []
    finally:
        connection.close()


def get_recipe_by_id(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM Recipes WHERE id = ?", (recipe_id,))
        return cursor.fetchone()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση συνταγής: {e}")
        return None

    finally:
        connection.close()


def get_steps(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT * FROM Steps
            WHERE recipe_id = ?
            ORDER BY step_number ASC
        """, (recipe_id,))
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση βημάτων: {e}")
        return []
    finally:
        connection.close()


def get_ingredients(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT Ingredients.name, Recipe_Ingredients.amount, Ingredients.id
            FROM Ingredients
            JOIN Recipe_Ingredients ON Ingredients.id = Recipe_Ingredients.ingredient_id
            WHERE Recipe_Ingredients.recipe_id = ?
        """, (recipe_id,))
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση υλικών: {e}")
        return []
    finally:
        connection.close()


def delete_recipe(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("DELETE FROM Recipes WHERE id = ?", (recipe_id,))

        connection.commit()
        print("Η συνταγή διαγράφηκε επιτυχώς!")

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά τη διαγραφή: {e}")

    finally:
        connection.close()


def delete_step(step_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM Steps WHERE id = ?", (step_id,))
        connection.commit()
        print("Το βήμα διαγράφηκε επιτυχώς!")

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά τη διαγραφή βήματος: {e}")
    finally:
        connection.close()


def clear_recipe_steps(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM Steps WHERE recipe_id = ?", (recipe_id,))
        connection.commit()
    except sqlite3.Error as e:
        print(f"Σφάλμα: {e}")
    finally:
        connection.close()


def clear_recipe_ingredients(recipe_id):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM Recipe_Ingredients WHERE recipe_id = ?", (recipe_id,))
        connection.commit()
    except sqlite3.Error as e:
        print(f"Σφάλμα: {e}")
    finally:
        connection.close() 


def update_recipe(recipe_id, title, category, difficulty, duration, servings=4):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE Recipes
            SET title = ?, category = ?, difficulty = ?, total_duration = ?, servings = ?
            WHERE id = ?
        """, (title, category, difficulty, duration, servings, recipe_id))

        connection.commit()
        print(f"Η συνταγή '{title}' ενημερώθηκε επιτυχώς!")

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την τροποποίηση: {e}")

    finally:
        connection.close()


def update_step(step_id, title, instruction, time_hours, time_minutes):
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE Steps
            SET title = ?, instruction = ?, time_hours = ?, time_minutes = ?
            WHERE id = ?
        """, (title, instruction, str(time_hours), str(time_minutes), step_id))

        connection.commit()
        print("Το βήμα ενημερώθηκε επιτυχώς!")

    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την τροποποίηση βήματος: {e}")
    finally:
        connection.close()



def get_all_categories():
    """Επιστρέφει όλες τις μοναδικές κατηγορίες από τη βάση (sorted)."""
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT DISTINCT category FROM Recipes WHERE category IS NOT NULL ORDER BY category ASC")
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση κατηγοριών: {e}")
        return []
    finally:
        connection.close()


def get_recipes_by_category(category):
    """Επιστρέφει όλες τις συνταγές μιας κατηγορίας (Αλφαβητικά)."""
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT * FROM Recipes 
            WHERE category = ? 
            ORDER BY title ASC
        """, (category,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Σφάλμα κατά την ανάκτηση συνταγών κατηγορίας: {e}")
        return []
    finally:
        connection.close()


def get_recipe_count():
    """Επιστρέφει τον συνολικό αριθμό συνταγών."""
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM Recipes")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"Σφάλμα: {e}")
        return 0
    finally:
        connection.close()


def recipe_exists(title, category):
    """Ελέγχει αν υπάρχει ήδη συνταγή με το ίδιο όνομα στην ίδια κατηγορία."""
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id FROM Recipes 
            WHERE LOWER(title) = LOWER(?) AND category = ?
        """, (title, category))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Σφάλμα: {e}")
        return False
    finally:
        connection.close()


def save_full_recipe(recipe_dict):
    """
    Αποθηκεύει μια πλήρη συνταγή (με υλικά και βήματα) σε ένα transaction.

    recipe_dict = {
        "title": str,
        "category": str,
        "difficulty": str,
        "total_duration": int,
        "ingredients": [{"name": str, "amount": str}, ...],
        "steps": [
            {
                "step_number": int,
                "title": str,
                "instruction": str,
                "time_hours": str,
                "time_minutes": str,
                "ingredients": [{"name": str, "amount": str}, ...]  # optional
            }, ...
        ]
    }

    Επιστρέφει (recipe_id, None) σε επιτυχία, (None, error_msg) σε αποτυχία.
    """
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1) Αποθήκευση συνταγής
        cursor.execute("""
            INSERT INTO Recipes (title, category, difficulty, total_duration, servings)
            VALUES (?, ?, ?, ?, ?)
        """, (
            recipe_dict["title"],
            recipe_dict.get("category", ""),
            recipe_dict.get("difficulty", ""),
            recipe_dict.get("total_duration", 0),
            recipe_dict.get("servings", 4)
        ))
        recipe_id = cursor.lastrowid

        # 2) Αποθήκευση υλικών συνταγής
        for ing in recipe_dict.get("ingredients", []):
            cursor.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?)", (ing["name"],))
            cursor.execute("SELECT id FROM Ingredients WHERE name = ?", (ing["name"],))
            ing_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO Recipe_Ingredients (recipe_id, ingredient_id, amount)
                VALUES (?, ?, ?)
            """, (recipe_id, ing_id, ing.get("amount", "")))

        # 3) Αποθήκευση βημάτων + υλικών βημάτων
        for step in recipe_dict.get("steps", []):
            cursor.execute("""
                INSERT INTO Steps (recipe_id, step_number, title, instruction, time_hours, time_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                step["step_number"],
                step.get("title", ""),
                step.get("instruction", ""),
                str(step.get("time_hours", "")),
                str(step.get("time_minutes", ""))
            ))
            step_id = cursor.lastrowid

            for ing in step.get("ingredients", []):
                cursor.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?)", (ing["name"],))
                cursor.execute("SELECT id FROM Ingredients WHERE name = ?", (ing["name"],))
                ing_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO Step_Ingredients (step_id, ingredient_id, amount)
                    VALUES (?, ?, ?)
                """, (step_id, ing_id, ing.get("amount", "")))

        connection.commit()
        print(f" Πλήρης συνταγή '{recipe_dict['title']}' αποθηκεύτηκε με ID: {recipe_id}")
        return recipe_id, None

    except sqlite3.Error as e:
        connection.rollback()
        error_msg = f"Transaction failed: {e}"
        print(f" {error_msg}")
        return None, error_msg
    except Exception as e:
        connection.rollback()
        error_msg = f"Unexpected error: {e}"
        print(f" {error_msg}")
        return None, error_msg
    finally:
        connection.close()


def update_full_recipe(recipe_id, recipe_dict):
    """
    Ενημερώνει μια πλήρη συνταγή (βασικά στοιχεία, υλικά και βήματα) σε ένα transaction.
    Αντικαθιστά τα παλιά υλικά και βήματα με τα νέα.
    """
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1) Ενημέρωση βασικών στοιχείων συνταγής
        cursor.execute("""
            UPDATE Recipes
            SET title = ?, category = ?, difficulty = ?, total_duration = ?, servings = ?
            WHERE id = ?
        """, (
            recipe_dict["title"],
            recipe_dict.get("category", ""),
            recipe_dict.get("difficulty", ""),
            recipe_dict.get("total_duration", 0),
            recipe_dict.get("servings", 4),
            recipe_id
        ))

        # 2) Διαγραφή παλιών υλικών και βημάτων (λόγω ON DELETE CASCADE τα Step_Ingredients και Recipe_Ingredients θα διαγραφούν)
        cursor.execute("DELETE FROM Recipe_Ingredients WHERE recipe_id = ?", (recipe_id,))
        cursor.execute("DELETE FROM Steps WHERE recipe_id = ?", (recipe_id,))

        # 3) Αποθήκευση νέων υλικών συνταγής
        for ing in recipe_dict.get("ingredients", []):
            cursor.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?)", (ing["name"],))
            cursor.execute("SELECT id FROM Ingredients WHERE name = ?", (ing["name"],))
            ing_id = cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO Recipe_Ingredients (recipe_id, ingredient_id, amount)
                VALUES (?, ?, ?)
            """, (recipe_id, ing_id, ing.get("amount", "")))

        # 4) Αποθήκευση νέων βημάτων + υλικών βημάτων
        for step in recipe_dict.get("steps", []):
            cursor.execute("""
                INSERT INTO Steps (recipe_id, step_number, title, instruction, time_hours, time_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                step["step_number"],
                step.get("title", ""),
                step.get("instruction", ""),
                str(step.get("time_hours", "")),
                str(step.get("time_minutes", ""))
            ))
            step_id = cursor.lastrowid

            for ing in step.get("ingredients", []):
                cursor.execute("INSERT OR IGNORE INTO Ingredients (name) VALUES (?)", (ing["name"],))
                cursor.execute("SELECT id FROM Ingredients WHERE name = ?", (ing["name"],))
                ing_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO Step_Ingredients (step_id, ingredient_id, amount)
                    VALUES (?, ?, ?)
                """, (step_id, ing_id, ing.get("amount", "")))

        connection.commit()
        print(f" Η συνταγή με ID {recipe_id} ενημερώθηκε πλήρως.")
        return True, None

    except sqlite3.Error as e:
        connection.rollback()
        error_msg = f"Transaction failed: {e}"
        print(f" {error_msg}")
        return False, error_msg
    except Exception as e:
        connection.rollback()
        error_msg = f"Unexpected error: {e}"
        print(f" {error_msg}")
        return False, error_msg
    finally:
        connection.close()


def seed_database():
    """
    Γεμίζει τη βάση με demo δεδομένα αν είναι κενή.
    Χρήσιμο για πρώτη εκτέλεση / testing.
    """
    if get_recipe_count() > 0:
        print("Η βάση έχει ήδη δεδομένα, παραλείπεται το seed.")
        return

    demo_recipes = [
        {
            "title": "Ψάρι στον ατμό με λεμόνι",
            "category": "Ψάρια",
            "difficulty": "Εύκολη",
            "total_duration": 25,
            "servings": 2,
            "ingredients": [
                {"name": "Φιλέτο ψαριού", "amount": "2 τεμ."},
                {"name": "Λεμόνι", "amount": "1 τεμ."},
                {"name": "Ελαιόλαδο", "amount": "3 κ.σ."},
                {"name": "Άνηθος", "amount": "1 ματσάκι"},
            ],
            "steps": [
                {"step_number": 1, "title": "Προετοιμασία", "instruction": "Πλύνετε το ψάρι και στεγνώστε το με χαρτί κουζίνας.", "time_hours": "", "time_minutes": "5"},
                {"step_number": 2, "title": "Ατμός", "instruction": "Τοποθετήστε το ψάρι στον ατμό με φέτες λεμονιού από πάνω.", "time_hours": "", "time_minutes": "15", "ingredients": [{"name": "Λεμόνι", "amount": "φέτες"}]},
                {"step_number": 3, "title": "Σερβίρισμα", "instruction": "Περιχύστε με ελαιόλαδο και πασπαλίστε άνηθο.", "time_hours": "", "time_minutes": "5", "ingredients": [{"name": "Ελαιόλαδο", "amount": "3 κ.σ."}, {"name": "Άνηθος", "amount": "1 ματσάκι"}]},
            ]
        },
        {
            "title": "Μακαρόνια με κιμά",
            "category": "Ζυμαρικά",
            "difficulty": "Εύκολη",
            "total_duration": 40,
            "servings": 4,
            "ingredients": [
                {"name": "Σπαγγέτι", "amount": "500 γρ."},
                {"name": "Κιμάς μοσχαρίσιος", "amount": "400 γρ."},
                {"name": "Τομάτα περασμένη", "amount": "1 κονσέρβα"},
                {"name": "Κρεμμύδι", "amount": "1 μεγάλο"},
            ],
            "steps": [
                {"step_number": 1, "title": "Σοτάρισμα", "instruction": "Σοτάρετε τον κιμά με το κρεμμύδι μέχρι να ροδίσει.", "time_hours": "", "time_minutes": "10", "ingredients": [{"name": "Κιμάς μοσχαρίσιος", "amount": "400 γρ."}, {"name": "Κρεμμύδι", "amount": "1 μεγάλο"}]},
                {"step_number": 2, "title": "Σάλτσα", "instruction": "Προσθέστε την τομάτα και αφήστε να σιγοβράσει.", "time_hours": "", "time_minutes": "20", "ingredients": [{"name": "Τομάτα περασμένη", "amount": "1 κονσέρβα"}]},
                {"step_number": 3, "title": "Βράσιμο ζυμαρικών", "instruction": "Βράστε τα μακαρόνια σε αλατισμένο νερό.", "time_hours": "", "time_minutes": "10", "ingredients": [{"name": "Σπαγγέτι", "amount": "500 γρ."}]},
            ]
        },
        {
            "title": "Μοσχαράκι κοκκινιστό",
            "category": "Κρέας",
            "difficulty": "Μέτρια",
            "total_duration": 90,
            "servings": 6,
            "ingredients": [
                {"name": "Μοσχαράκι", "amount": "800 γρ."},
                {"name": "Κρεμμύδι", "amount": "2 μεγάλα"},
                {"name": "Σκόρδο", "amount": "2 σκελίδες"},
                {"name": "Ντομάτα", "amount": "3 ώριμες"},
            ],
            "steps": [
                {"step_number": 1, "title": "Κατσάρωμα", "instruction": "Κόψτε το κρέας σε μερίδες και κατσαρώστε το.", "time_hours": "", "time_minutes": "10"},
                {"step_number": 2, "title": "Κοκκίνισμα", "instruction": "Προσθέστε κρεμμύδι, σκόρδο και ντομάτα. Ανακατέψτε καλά.", "time_hours": "", "time_minutes": "5", "ingredients": [{"name": "Κρεμμύδι", "amount": "2 μεγάλα"}, {"name": "Σκόρδο", "amount": "2 σκελίδες"}, {"name": "Ντομάτα", "amount": "3 ώριμες"}]},
                {"step_number": 3, "title": "Μαγείρεμα", "instruction": "Προσθέστε νερό και αφήστε σε χαμηλή φωτιά μέχρι να μαλακώσει.", "time_hours": "1", "time_minutes": "15", "ingredients": [{"name": "Μοσχαράκι", "amount": "800 γρ."}]},
            ]
        },
        {
            "title": "Πατάτες φούρνου με μυρωδικά",
            "category": "Φούρνος",
            "difficulty": "Εύκολη",
            "total_duration": 60,
            "servings": 4,
            "ingredients": [
                {"name": "Πατάτες", "amount": "1 κιλό"},
                {"name": "Ελαιόλαδο", "amount": "1/2 φλ."},
                {"name": "Ρίγανη", "amount": "1 κ.σ."},
                {"name": "Λεμόνι", "amount": "1/2 τεμ."},
            ],
            "steps": [
                {"step_number": 1, "title": "Προετοιμασία", "instruction": "Κόψτε τις πατάτες σε μικρά κομμάτια.", "time_hours": "", "time_minutes": "10"},
                {"step_number": 2, "title": "Μαρινάρισμα", "instruction": "Ανακατέψτε με ελαιόλαδο, ρίγανη και χυμό λεμονιού.", "time_hours": "", "time_minutes": "5", "ingredients": [{"name": "Ελαιόλαδο", "amount": "1/2 φλ."}, {"name": "Ρίγανη", "amount": "1 κ.σ."}, {"name": "Λεμόνι", "amount": "1/2 τεμ."}]},
                {"step_number": 3, "title": "Ψήσιμο", "instruction": "Ψήστε σε προθερμασμένο φούρνο στους 200°C.", "time_hours": "", "time_minutes": "45"},
            ]
        },
        {
            "title": "Κοτόπουλο Air Fryer",
            "category": "Air Fryer",
            "difficulty": "Εύκολη",
            "total_duration": 35,
            "servings": 2,
            "ingredients": [
                {"name": "Κοτόπουλο φιλέτο", "amount": "2 τεμ."},
                {"name": "Πάπρικα", "amount": "1 κ.γ."},
                {"name": "Ελαιόλαδο", "amount": "1 κ.σ."},
                {"name": "Αλάτι", "amount": "1 κ.γ."},
            ],
            "steps": [
                {"step_number": 1, "title": "Μαρινάρισμα", "instruction": "Ανακατέψτε το κοτόπουλο με μπαχαρικά και λάδι.", "time_hours": "", "time_minutes": "10", "ingredients": [{"name": "Πάπρικα", "amount": "1 κ.γ."}, {"name": "Ελαιόλαδο", "amount": "1 κ.σ."}, {"name": "Αλάτι", "amount": "1 κ.γ."}]},
                {"step_number": 2, "title": "Μαγείρεμα", "instruction": "Τοποθετήστε στο Air Fryer στους 180°C.", "time_hours": "", "time_minutes": "20", "ingredients": [{"name": "Κοτόπουλο φιλέτο", "amount": "2 τεμ."}]},
                {"step_number": 3, "title": "Αναμονή", "instruction": "Αφήστε 5 λεπτά να ξεκουραστεί πριν το κόψετε.", "time_hours": "", "time_minutes": "5"},
            ]
        },
        {
            "title": "Vegan μπολ με κινόα",
            "category": "Vegan",
            "difficulty": "Εύκολη",
            "total_duration": 30,
            "servings": 1,
            "ingredients": [
                {"name": "Κινόα", "amount": "200 γρ."},
                {"name": "Αβοκάντο", "amount": "1 τεμ."},
                {"name": "Ντοματίνια", "amount": "10 τεμ."},
                {"name": "Χούμους", "amount": "3 κ.σ."},
            ],
            "steps": [
                {"step_number": 1, "title": "Βράσιμο κινόας", "instruction": "Βράστε την κινόα σε 2 φλιτζάνια νερό.", "time_hours": "", "time_minutes": "15", "ingredients": [{"name": "Κινόα", "amount": "200 γρ."}]},
                {"step_number": 2, "title": "Προετοιμασία λαχανικών", "instruction": "Κόψτε το αβοκάντο και τα ντοματίνια.", "time_hours": "", "time_minutes": "5", "ingredients": [{"name": "Αβοκάντο", "amount": "1 τεμ."}, {"name": "Ντοματίνια", "amount": "10 τεμ."}]},
                {"step_number": 3, "title": "Συναρμολόγηση", "instruction": "Ανακατέψτε όλα τα υλικά σε μπολ και προσθέστε χούμους.", "time_hours": "", "time_minutes": "10", "ingredients": [{"name": "Χούμους", "amount": "3 κ.σ."}]},
            ]
        },
    ]

    for recipe in demo_recipes:
        rid, err = save_full_recipe(recipe)
        if err:
            print(f"Σφάλμα στο seed: {err}")

    print("✅ Demo δεδομένα προστέθηκαν επιτυχώς!")


if __name__ == "__main__":
    setup_database()
    seed_database()
