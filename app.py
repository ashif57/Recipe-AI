import json
from flask import Flask, request, render_template
from dotenv import load_dotenv
import os

load_dotenv()

# Try to import IBM Watson AI, but provide fallback if not available
try:
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    from ibm_watsonx_ai import Credentials
    
    credentials = Credentials(
        url="https://us-south.ml.cloud.ibm.com",
        api_key=os.getenv("IBM_API_KEY")
    )
    
    # Initialize the model
    model = ModelInference(
        model_id="ibm/granite-13b-chat-v2",
        params={
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 400,
            GenParams.TEMPERATURE: 0.7,
            GenParams.STOP_SEQUENCES: ["\n\n"]
        },
        credentials=credentials,
        project_id=os.getenv("IBM_PROJECT_ID")
    )
    AI_AVAILABLE = True
except Exception as e:
    print(f"Watson AI not available: {e}")
    print("Using fallback recipe generation...")
    AI_AVAILABLE = False
    model = None





app = Flask(__name__)

with open("recipes50.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)


def find_recipes_by_ingredients(user_ingredients):
    matched = []
    for recipe in recipes:
        match_count = sum(
            1 for ing in user_ingredients if any(ing.lower() in r.lower() for r in recipe['ingredients'])
        )
        if match_count > 0:
            matched.append((recipe, match_count))
    matched.sort(key=lambda x: -x[1])
    return [r[0] for r in matched[:3]]  # top 3 matches

def generate_granite_response(recipe_title, ingredients, original_recipe=None):
    if AI_AVAILABLE and model:
        # Try to use AI generation
        prompt = f"""Suggest a step-by-step recipe for "{recipe_title}" using these ingredients:\n{', '.join(ingredients)}.\n
If something is missing, offer substitutions. Provide only cooking instructions in clear numbered steps."""
        
        try:
            response = model.generate_text(prompt=prompt)
            return response
        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fall back to original recipe if AI fails
            return generate_fallback_recipe(recipe_title, ingredients, original_recipe)
    else:
        # Use fallback recipe generation
        return generate_fallback_recipe(recipe_title, ingredients, original_recipe)

def generate_fallback_recipe(recipe_title, user_ingredients, original_recipe):
    """Generate recipe instructions using the original recipe data as a base"""
    if original_recipe and 'steps' in original_recipe:
        # Use the original recipe steps as a base
        steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(original_recipe['steps'])])
        
        # Add a note about ingredient substitutions
        ingredient_note = f"\nNote: This recipe has been adapted for your available ingredients: {', '.join(user_ingredients)}"
        
        # Check for missing ingredients and suggest substitutions
        original_ingredients = [ing.lower() for ing in original_recipe.get('ingredients', [])]
        user_ingredients_lower = [ing.lower().strip() for ing in user_ingredients]
        
        missing_ingredients = []
        for orig_ing in original_ingredients:
            if not any(user_ing in orig_ing or orig_ing in user_ing for user_ing in user_ingredients_lower):
                missing_ingredients.append(orig_ing)
        
        if missing_ingredients:
            substitution_note = f"\n\nMissing ingredients you might want to substitute or add:\n"
            substitution_note += "\n".join([f"• {ing}" for ing in missing_ingredients[:5]])  # Limit to 5
        else:
            substitution_note = "\n\nYou have most of the ingredients needed for this recipe!"
        
        return steps + ingredient_note + substitution_note
    else:
        # Generic recipe template
        return f"""Here's a basic recipe for {recipe_title} using your ingredients:

1. Prepare all your ingredients: {', '.join(user_ingredients)}
2. Heat a pan or pot over medium heat
3. Start with aromatics like onions and garlic if available
4. Add your main protein or vegetables
5. Season with salt, pepper, and any available spices
6. Cook until ingredients are properly done
7. Taste and adjust seasoning as needed
8. Serve hot and enjoy!

Note: This is a basic template. For detailed instructions, please ensure your Watson AI service is properly configured."""

@app.route("/", methods=["GET", "POST"])
def index():
    matched_recipes = []
    generated_instructions = []

    if request.method == "POST":
        ingredients = [ing.strip() for ing in request.form["ingredients"].split(",")]
        matched = find_recipes_by_ingredients(ingredients)

        for r in matched:
            ai_steps = generate_granite_response(r["title"], ingredients, r)
            generated_instructions.append({
                "title": r["title"],
                "steps": ai_steps
            })

    return render_template("index.html", recipes=generated_instructions)


if __name__ == "__main__":
    app.run(debug=True)
