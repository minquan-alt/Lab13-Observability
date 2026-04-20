from __future__ import annotations

import time

from .incidents import STATE

CORPUS = {
    # =========================
    # DISH DOCS
    # =========================
    "fried_rice": [
        "Fried rice is best made with cold cooked rice so the grains stay separate.",
        "Core ingredients: cooked rice, egg, garlic, onion, soy sauce, oil, mixed vegetables.",
        "Basic steps: stir-fry garlic and onion, scramble eggs, add rice, season, then add vegetables.",
        "Use high heat and keep stirring to avoid clumping.",
    ],

    "fried_rice_variants": [
        "Chicken fried rice can add diced chicken breast or thigh for more protein.",
        "Shrimp fried rice works well with a small amount of fish sauce and spring onion.",
        "Vegetable fried rice can use corn, carrot, peas, mushroom, and tofu.",
        "For Thai-style fried rice, use jasmine rice and a touch of fish sauce or oyster sauce.",
    ],

    "pho_bo": [
        "Beef pho uses beef bones, ginger, onion, star anise, cinnamon, cloves, fish sauce, beef slices, and rice noodles.",
        "The broth is simmered slowly so it becomes clear, aromatic, and rich.",
        "Roast ginger and onion first to improve aroma before simmering the bones.",
        "Skim foam regularly and season the broth gradually.",
    ],

    "pho_bo_variants": [
        "Northern-style pho usually has a cleaner broth and more restrained seasoning.",
        "Southern-style pho is often sweeter and served with more herbs and bean sprouts.",
        "Pho tai uses thin slices of raw beef cooked by hot broth.",
        "Pho bo vien uses beef meatballs instead of sliced beef.",
    ],

    "scrambled_eggs": [
        "Scrambled eggs use eggs, butter, and salt; milk is optional.",
        "Cook on low heat and stir gently for a creamy texture.",
        "Remove from heat while the eggs are still slightly soft because residual heat will finish cooking.",
    ],

    "scrambled_eggs_variants": [
        "Soft scrambled eggs should be cooked slowly for a custard-like texture.",
        "Firm scrambled eggs are cooked a little longer for a drier texture.",
        "Cheese scrambled eggs can include cheddar or parmesan for a richer taste.",
    ],

    "pancake": [
        "Basic pancakes use flour, milk, egg, sugar, butter, and a little baking powder if available.",
        "Mix the batter until just combined; overmixing makes pancakes dense.",
        "Cook on medium heat and flip when bubbles appear on the surface.",
    ],

    "pancake_variants": [
        "Banana pancakes can replace part of the sugar with ripe banana for sweetness.",
        "Buttermilk pancakes are slightly tangier and often fluffier.",
        "Protein pancakes can include oats, yogurt, or protein powder.",
    ],

    "grilled_chicken": [
        "Grilled chicken usually needs chicken, garlic, pepper, salt, soy sauce, and a little oil.",
        "Marinate at least 30 minutes to improve flavor.",
        "Let the chicken rest after cooking to keep the juices inside.",
    ],

    "grilled_chicken_variants": [
        "Honey garlic chicken tastes sweeter and more caramelized.",
        "Lemongrass chicken has a more fragrant Vietnamese-style flavor.",
        "Spicy chicken can add chili flakes or chili sauce to the marinade.",
    ],

    "vegetable_soup": [
        "Vegetable soup can use carrot, potato, onion, cabbage, salt, pepper, and water or stock.",
        "Add harder vegetables first and softer vegetables later so everything cooks evenly.",
        "Simmer gently rather than boiling too hard.",
    ],

    "vegetable_soup_variants": [
        "Creamy vegetable soup can be blended after cooking and finished with milk or cream.",
        "Clear vegetable soup keeps the broth light and simple.",
        "Miso-style vegetable soup can use tofu and seaweed for extra umami.",
    ],

    "stir_fried_vegetables": [
        "Stir-fried vegetables often use broccoli, carrot, garlic, oil, and soy sauce.",
        "Use high heat and short cooking time to keep vegetables crisp.",
        "Add a small splash of water and cover briefly if the vegetables are too firm.",
    ],

    "stir_fried_vegetables_variants": [
        "Garlic butter vegetables taste richer and more savory.",
        "Oyster sauce vegetables are slightly sweeter and more glossy.",
        "Spicy stir-fried vegetables can add chili or black pepper.",
    ],

    "boiled_egg": [
        "Soft-boiled eggs are cooked for about 6 minutes.",
        "Hard-boiled eggs are cooked for about 10 minutes.",
        "Cool the eggs in cold water after boiling so they peel more easily.",
    ],

    "salad_basic": [
        "A basic salad uses lettuce, tomato, cucumber, olive oil, and vinegar.",
        "Add dressing right before serving to keep the vegetables fresh.",
        "Season lightly and adjust after tasting.",
    ],

    "salad_variants": [
        "Caesar-style salad can include croutons, cheese, and creamy dressing.",
        "Fruit salad can use banana, apple, grapes, and yogurt.",
        "Protein salad can add chicken, egg, tuna, or tofu.",
    ],

    # =========================
    # INGREDIENT DOCS
    # =========================
    "ingredient_sugar": [
        "Sugar adds sweetness and can balance sour, salty, or bitter flavors.",
        "To make a dish sweeter, increase sugar slowly and taste after each small adjustment.",
        "If a recipe becomes too sweet, add a little acid such as lemon juice or vinegar to rebalance it.",
    ],

    "ingredient_salt": [
        "Salt enhances flavor and makes other ingredients taste clearer.",
        "Add salt gradually because it is easier to add more than to fix an over-salted dish.",
        "If a dish tastes flat, a small amount of salt often improves the overall flavor.",
    ],

    "ingredient_soy_sauce": [
        "Soy sauce adds saltiness, color, and umami.",
        "Use soy sauce carefully in dishes that already contain salt or fish sauce.",
        "For a lighter taste, use less soy sauce and add more aromatics instead.",
    ],

    "ingredient_fish_sauce": [
        "Fish sauce adds savory depth and a distinct Vietnamese flavor.",
        "Use it in small amounts and adjust slowly because the aroma can become strong.",
        "Fish sauce works well in fried rice, noodle dishes, and marinades.",
    ],

    "ingredient_oil": [
        "Oil helps transfer heat and prevents sticking.",
        "Too much oil makes a dish greasy, while too little may cause burning or sticking.",
        "For lighter food, use just enough oil to coat the pan.",
    ],

    "ingredient_butter": [
        "Butter adds richness, aroma, and a creamy mouthfeel.",
        "Use butter for eggs, pancakes, and sauces when you want a softer flavor.",
        "Too much butter can make a dish heavy, so add gradually.",
    ],

    "ingredient_egg": [
        "Eggs add protein, richness, and binding power.",
        "Eggs can be scrambled, boiled, fried, or used in batter.",
        "For softer texture, cook eggs on low heat and avoid overcooking.",
    ],

    "ingredient_rice": [
        "Cold cooked rice is better for fried rice because it is drier and separates more easily.",
        "Fresh rice is softer and can clump, so it should be cooled before stir-frying.",
        "Jasmine rice is fragrant and works well in many Asian dishes.",
    ],

    "ingredient_garlic": [
        "Garlic adds aroma and savory depth.",
        "Add garlic early in cooking to release fragrance, but do not burn it.",
        "Minced garlic cooks faster than sliced garlic.",
    ],

    "ingredient_onion": [
        "Onion adds sweetness and aroma when cooked.",
        "Cooking onion longer makes it sweeter and softer.",
        "For broth, onion can be roasted first to deepen flavor.",
    ],

    "ingredient_ginger": [
        "Ginger adds warmth and freshness.",
        "Roasted ginger gives a deeper aroma in soups and broths.",
        "Use ginger sparingly because too much can overpower the dish.",
    ],

    "ingredient_lime": [
        "Lime adds acidity and freshness.",
        "A small amount of lime can make a dish brighter and less heavy.",
        "Add lime near the end so the flavor stays fresh.",
    ],

    "ingredient_chili": [
        "Chili adds heat and can balance sweetness or richness.",
        "Use chili flakes, fresh chili, or chili sauce depending on the dish.",
        "If a dish becomes too spicy, add sugar, dairy, or more base ingredients to soften the heat.",
    ],

    "ingredient_milk": [
        "Milk can make batter smoother and scrambled eggs softer.",
        "Use milk in small amounts so the dish does not become watery.",
        "For richer texture, milk can be replaced partly with cream or yogurt in some recipes.",
    ],

    "ingredient_cream": [
        "Cream adds richness and a thicker texture.",
        "Cream works well in soups, sauces, and some desserts.",
        "Use cream carefully because too much can make the dish heavy.",
    ],

    "ingredient_vinegar": [
        "Vinegar adds acidity and helps balance sweetness or oiliness.",
        "A small amount of vinegar can brighten salads and some sauces.",
        "Add vinegar gradually because the sour taste can become sharp quickly.",
    ],

    "ingredient_basil": [
        "Basil adds a fragrant herbal note.",
        "Add basil near the end of cooking to preserve its aroma.",
        "Basil works well with tomato dishes, soups, and some stir-fries.",
    ],

    "ingredient_mushroom": [
        "Mushrooms add umami and a meaty texture.",
        "Different mushrooms cook at different speeds, so cut them to similar size.",
        "Mushrooms work well in soup, fried rice, and stir-fries.",
    ],

    # =========================
    # TECHNIQUE / ADJUSTMENT DOCS
    # =========================
    "adjust_more_sweet": [
        "To make a dish sweeter, add sugar, honey, or ripe fruit in small increments.",
        "If the dish is already salty or sour, sweetness can help balance the flavor.",
        "Taste after each adjustment to avoid over-sweetening.",
    ],

    "adjust_less_sweet": [
        "To reduce sweetness, add a little salt, acid, or more base ingredients.",
        "You can also dilute the dish slightly if the recipe supports it.",
    ],

    "adjust_more_savory": [
        "To make a dish more savory, add soy sauce, fish sauce, salt, mushrooms, or stock.",
        "Savory flavor is often improved by aromatics like garlic and onion.",
    ],

    "adjust_more_salty": [
        "To make a dish saltier, add salt, soy sauce, or fish sauce gradually.",
        "If the dish becomes too salty, add water, rice, vegetables, or an unsalted base.",
    ],

    "adjust_more_spicy": [
        "To make a dish spicier, add chili, chili flakes, pepper, or chili oil.",
        "Add spice in small steps because heat builds quickly.",
    ],

    "adjust_less_spicy": [
        "To reduce spiciness, add sugar, dairy, rice, or more plain base ingredients.",
        "A squeeze of lime can help balance heat in some dishes, but use carefully.",
    ],

    "adjust_more_fatty": [
        "To make a dish richer or more fatty, add butter, cream, oil, or fatty meat in moderation.",
        "Add richness slowly so the dish does not become too heavy.",
    ],

    "adjust_more_fresh": [
        "To make a dish feel fresher, add herbs, lime, cucumber, or a lighter dressing.",
        "Freshness is often improved by reducing heavy oil or sauce.",
    ],

    "adjust_more_aromatic": [
        "To improve aroma, use garlic, onion, ginger, herbs, toasted spices, or roasted ingredients.",
        "Aromatics are often added early for depth or late for freshness depending on the recipe.",
    ],

    "adjust_thicker": [
        "To make soup or sauce thicker, simmer longer, reduce liquid, or add ingredients like egg, starch, or cream where appropriate.",
        "Stir frequently when reducing so the mixture does not burn.",
    ],

    "adjust_thinner": [
        "To make a dish thinner, add a little water, stock, milk, or broth depending on the recipe.",
        "Add liquid gradually so you do not over-dilute the flavor.",
    ],

    # =========================
    # SAFETY / QUALITY
    # =========================
    "food_safety": [
        "Keep raw meat separate from ready-to-eat food to avoid cross-contamination.",
        "Cook poultry thoroughly and refrigerate leftovers within two hours.",
        "Wash hands, utensils, and cutting boards after handling raw ingredients.",
    ],

    "storage": [
        "Store herbs in the refrigerator or in water depending on the type.",
        "Use airtight containers to keep dry ingredients fresh longer.",
        "Label leftovers with the date so they are easier to track.",
    ],

    "recipe_planning": [
        "A good recipe lists ingredients, quantities, steps, and estimated cooking time.",
        "Prep all ingredients before cooking to make the process smoother.",
    ],
}


def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            return docs
    return ["No domain document matched. Use general fallback answer."]
