import Database

class Ingredient:
    def __init__(self, ingredient_id, name, amount):
        self.ingredient_id = ingredient_id
        self.name = name
        self.amount = amount

    def __repr__(self):
        return f"Ingredient(id={self.ingredient_id}, name={self.name!r}, amount={self.amount!r})"

    def __str__(self):
        return f"{self.amount} {self.name}" if self.amount else self.name

    def to_dict(self):
        return {
            "id": self.ingredient_id,
            "name": self.name,
            "amount": self.amount
        }


class Step:
    def __init__(self, step_id, step_number, title, instruction, time_hours, time_minutes):
        self.step_id = step_id
        self.step_number = step_number
        self.title = title
        self.instruction = instruction
        self.time_hours = time_hours if time_hours is not None else ""
        self.time_minutes = time_minutes if time_minutes is not None else ""
        self.ingredients = []

    def __repr__(self):
        return (f"Step(id={self.step_id}, num={self.step_number}, title={self.title!r}, "
                f"duration={self.get_duration_minutes()}min)")

    def __str__(self):
        return f"Βήμα {self.step_number}: {self.title}"

    def get_duration_minutes(self):
        """Υπολογίζει τη διάρκεια του βήματος σε λεπτά. Αν δεν είναι αριθμοί, επιστρέφει 0."""
        try:
            h = int(self.time_hours) if str(self.time_hours).strip().isdigit() else 0
            m = int(self.time_minutes) if str(self.time_minutes).strip().isdigit() else 0
            return h * 60 + m
        except (ValueError, TypeError):
            return 0

    def get_duration_text(self):
        """Επιστρέφει ανθρώπινα αναγνώσιμο κείμενο διάρκειας."""
        parts = []
        if str(self.time_hours).strip().isdigit() and int(self.time_hours) > 0:
            parts.append(f"{self.time_hours} ώρες")
        if str(self.time_minutes).strip().isdigit() and int(self.time_minutes) > 0:
            parts.append(f"{self.time_minutes} λεπτά")
        return ", ".join(parts) if parts else "—"

    def to_dict(self):
        return {
            "id": self.step_id,
            "step_number": self.step_number,
            "title": self.title,
            "instruction": self.instruction,
            "time_hours": self.time_hours,
            "time_minutes": self.time_minutes,
            "duration_minutes": self.get_duration_minutes(),
            "ingredients": [ing.to_dict() for ing in self.ingredients]
        }


class Recipe:
    def __init__(self, recipe_id, title, category, difficulty, total_duration):
        self.recipe_id = recipe_id
        self.title = title
        self.category = category
        self.difficulty = difficulty
        self.total_duration = total_duration
        self.steps = []
        self.ingredients = []

    def __repr__(self):
        return (f"Recipe(id={self.recipe_id}, title={self.title!r}, "
                f"category={self.category!r}, steps={len(self.steps)})")

    def __str__(self):
        return f"{self.title} ({self.category}) — {self.difficulty}"

    def validate(self):
        """Ελέγχει αν η συνταγή έχει έγκυρα βασικά πεδία."""
        errors = []
        if not self.title or not str(self.title).strip():
            errors.append("Το όνομα συνταγής είναι υποχρεωτικό.")
        if not self.category:
            errors.append("Η κατηγορία είναι υποχρεωτική.")
        return errors

    def is_valid(self):
        return len(self.validate()) == 0

    def load_details(self):
        """Φορτώνει βήματα και υλικά από τη βάση."""
        steps_data = Database.get_steps(self.recipe_id)
        self.steps = []
        for step in steps_data:
            # Columns: id(0), recipe_id(1), step_number(2), title(3), instruction(4), time_hours(5), time_minutes(6)
            s = Step(step[0], step[2], step[3], step[4], step[5], step[6])
            step_ing_data = Database.get_step_ingredients(step[0])
            for ing in step_ing_data:
                s.ingredients.append(Ingredient(ing[2], ing[0], ing[1]))
            self.steps.append(s)

        ingredients_data = Database.get_ingredients(self.recipe_id)
        self.ingredients = []
        for ingredient in ingredients_data:
            self.ingredients.append(Ingredient(ingredient[2], ingredient[0], ingredient[1]))

    def add_step(self, step_number, title, instruction, time_hours="", time_minutes="", ingredients=None):
        """Προσθέτει ένα βήμα στο αντικείμενο (χωρίς αποθήκευση στη βάση ακόμα)."""
        s = Step(None, step_number, title, instruction, time_hours, time_minutes)
        if ingredients:
            for ing_data in ingredients:
                s.ingredients.append(Ingredient(None, ing_data["name"], ing_data.get("amount", "")))
        self.steps.append(s)
        return s

    def add_ingredient(self, name, amount=""):
        """Προσθέτει ένα υλικό στο αντικείμενο (χωρίς αποθήκευση στη βάση ακόμα)."""
        ing = Ingredient(None, name, amount)
        self.ingredients.append(ing)
        return ing

    def get_total_duration_text(self):
        """Επιστρέφει τη συνολική διάρκεια σε αναγνώσιμο κείμενο."""
        if not self.total_duration:
            return "—"
        hours = self.total_duration // 60
        mins = self.total_duration % 60
        parts = []
        if hours > 0:
            parts.append(f"{hours} ώρες")
        if mins > 0:
            parts.append(f"{mins} λεπτά")
        return ", ".join(parts) if parts else "—"

    def get_ingredients_summary(self):
        """Επιστρέφει συνοπτικό κείμενο υλικών."""
        if not self.ingredients:
            return ""
        return ", ".join([str(ing) for ing in self.ingredients[:5]])

    def to_dict(self):
        """Επιστρέφει πλήρη αναπαράσταση σε dictionary (χρήσιμο για JSON/export)."""
        return {
            "id": self.recipe_id,
            "title": self.title,
            "category": self.category,
            "difficulty": self.difficulty,
            "total_duration": self.total_duration,
            "total_duration_text": self.get_total_duration_text(),
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "steps": [step.to_dict() for step in self.steps]
        }

    # ── Υπάρχουσες μέθοδοι (διατηρούνται για backward compatibility) ──

    def save(self):
        """Αποθηκεύει μόνο τη βασική συνταγή (χωρίς βήματα/υλικά). Χρησιμοποιείστε RecipeManager.create_recipe() για πλήρη αποθήκευση."""
        recipe_id = Database.save_new_recipe(
            self.title, self.category, self.difficulty, self.total_duration
        )
        self.recipe_id = recipe_id
        return recipe_id

    def delete(self):
        Database.delete_recipe(self.recipe_id)

    def update(self):
        Database.update_recipe(
            self.recipe_id, self.title, self.category, self.difficulty, self.total_duration
        )



#Κύριο interface για το UI-------------------------------------------------------


class RecipeManager:
    """
    Ο συνθετικός κρίκος, συνδεέι το UI με το Model και τη Database.
    Χειρίζεται όλες τις λειτουργίες: CRUD, αναζήτηση, φόρτωμα κατηγοριών.
    """

    # Κατηγορίες που εμφανίζονται πάντα στο UI (merged με βάση)
    DEFAULT_CATEGORIES = [
        "Ψάρια",
        "Ζυμαρικά",
        "Κρέας",
        "Φούρνος",
        "Air Fryer",
        "Vegan",
    ]

    def __init__(self, auto_seed=True):
        Database.setup_database()
        if auto_seed:
            Database.seed_database()

    def get_categories(self):
        """
        Επιστρέφει όλες τις κατηγορίες (default + από βάση), χωρίς διπλότυπα, sorted.
        """
        db_cats = Database.get_all_categories()
        merged = list(dict.fromkeys(self.DEFAULT_CATEGORIES + db_cats))
        return merged

    def get_recipes_by_category(self, category):
        """
        Επιστρέφει λίστα από Recipe objects με φορτωμένα details.
        """
        rows = Database.get_recipes_by_category(category)
        recipes = []
        for row in rows:
            recipe = Recipe(row[0], row[1], row[2], row[3], row[4])
            recipe.load_details()
            recipes.append(recipe)
        return recipes

    def get_all_recipes(self):
        """
        Επιστρέφει ΟΛΕΣ τις συνταγές με φορτωμένα details.
        """
        rows = Database.get_all_recipes()
        recipes = []
        for row in rows:
            recipe = Recipe(row[0], row[1], row[2], row[3], row[4])
            recipe.load_details()
            recipes.append(recipe)
        return recipes

    def get_recipe_by_id(self, recipe_id):
        """
        Επιστρέφει ένα Recipe object με φορτωμένα details.
        """
        row = Database.get_recipe_by_id(recipe_id)
        if not row:
            return None
        recipe = Recipe(row[0], row[1], row[2], row[3], row[4])
        recipe.load_details()
        return recipe

    def search_recipes(self, search_term):
        """
        Αναζήτηση με φορτωμένα details.
        """
        if search_term.strip() == "":
            rows = Database.get_all_recipes()
        else:
            rows = Database.find_recipes(search_term)

        recipes = []
        for row in rows:
            recipe = Recipe(row[0], row[1], row[2], row[3], row[4])
            recipe.load_details()
            recipes.append(recipe)
        return recipes

    def create_recipe(self, title, category, difficulty, total_duration, ingredients_list, steps_list):
        """
        Δημιουργεί και αποθηκεύει μια ΠΛΗΡΗ συνταγή σε ένα transaction.

        ingredients_list: [{"name": str, "amount": str}, ...]
        steps_list: [
            {
                "step_number": int,
                "title": str,
                "instruction": str,
                "time_hours": str,
                "time_minutes": str,
                "ingredients": [{"name": str, "amount": str}, ...]  # optional
            }, ...
        ]

        Επιστρέφει (Recipe, None) ή (None, error_message).
        """
        # Validation
        temp_recipe = Recipe(None, title, category, difficulty, total_duration)
        errors = temp_recipe.validate()
        if errors:
            return None, " ".join(errors)

        if Database.recipe_exists(title, category):
            return None, f"Η συνταγή '{title}' υπάρχει ήδη στην κατηγορία '{category}'."

        recipe_dict = {
            "title": title,
            "category": category,
            "difficulty": difficulty,
            "total_duration": total_duration,
            "ingredients": ingredients_list,
            "steps": steps_list
        }

        recipe_id, err = Database.save_full_recipe(recipe_dict)
        if err:
            return None, err

        recipe = self.get_recipe_by_id(recipe_id)
        return recipe, None

    def delete_recipe(self, recipe_id):
        """Διαγράφει μια συνταγή και επιστρέφει True/False."""
        try:
            Database.delete_recipe(recipe_id)
            return True
        except Exception as e:
            print(f"Σφάλμα διαγραφής: {e}")
            return False

    def update_recipe_basic(self, recipe_id, title, category, difficulty, total_duration):
        """Ενημερώνει τα βασικά στοιχεία μιας συνταγής."""
        try:
            Database.update_recipe(recipe_id, title, category, difficulty, total_duration)
            return True
        except Exception as e:
            print(f"Σφάλμα ενημέρωσης: {e}")
            return False

    def get_recipe_count(self):
        """Επιστρέφει τον συνολικό αριθμό συνταγών."""
        return Database.get_recipe_count()



# παλιές συναρτήσεις


def load_recipes_from_search(search_term):
    """Παλιά συνάρτηση — διατηρείται για συμβατότητα."""
    mgr = RecipeManager(auto_seed=False)
    return mgr.search_recipes(search_term)
