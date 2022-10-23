from typing import Dict
import pandas as pd
from typing import Dict

def create_pizza_ingredients(df_pizza_types) -> Dict:
    """
    Generate a DataFrame containing each pizza as Keys and the
    ingredients as values (strings).
    """
    pizza_ingredients = {}
    for i in range(df_pizza_types.shape[0]):
        pizza_ingredients[df_pizza_types.loc[i, "pizza_type_id"]] = df_pizza_types.loc[i, "ingredients"]
    return pizza_ingredients

def create_ingredients(pizza_ingredients):
    """
    Create a dictionary with the amount of each ingredient we need.
    By default it starts as 0.
    """
    ingredients = {}
    for value in pizza_ingredients.values():
        particular_ingredients = value.split(", ")
        for ingredient in particular_ingredients:
            if ingredient not in ingredients:
                ingredients[ingredient] = 0
    return ingredients

def obtain_prices(df_pizzas):
    """
    DataFrame containing the price of each pizza
    """
    return  df_pizzas.groupby("pizza_type_id").sum()/3

def create_weekly_pizzas(df_orders, df_order_details, df_prices):
    """
    Create a new DataFrame representing the number of pizzas sold each
    week of 2015. This information helps us to compute the optimal number
    of pizzas we need to make to maximize the profits. We do this by computing
    the weekly average number of pizzas sold for each type. Then, we use the
    average profit margin of pizzas in USA, 15%, to calculate the optimal number
    of pizzas to make in order to lose as little money as possible.
    For each pizza type, we add the total money we would have lost each week
    if we had made a certain amount of pizzas. Then we pick the amount of
    pizzas with lhe least loses as optimal for each type. It is important to note
    that we have considered that the ingredients bought expire in a week, so there
    is no chnave they can be used the following week.
    """
    df_weekly_pizzas = pd.DataFrame()
    df_weekly_pizzas["pizza"] = pizza_ingredients.keys()
    df_weekly_pizzas["week 1"] = 0
    count = 0
    day = "01"
    i = 1
    j = 1
    # i represents the order id, j represnts the order details for each order id
    while i < df_orders.shape[0]:
        date = df_orders.loc[i, "date"]
        if date[:2] != day:
            count += 1
            day = date[:2]
            if count % 7 == 0:
                df_weekly_pizzas[f"week {int(count / 7) + 1}"] = 0
        while df_order_details.loc[j, "order_id"] == i:
            pizza = df_order_details.loc[j, "pizza_id"]
            quantity = df_order_details.loc[j, "quantity"]
            if pizza[-2] != "_":
                # We check this beacuse the greek pizza can be xl or xxl.
                pizza = pizza[:9]
            else:
                pizza = pizza[:-2]
            index = df_weekly_pizzas[df_weekly_pizzas["pizza"] == pizza].index
            df_weekly_pizzas.loc[index, f"week {int(count / 7) + 1}"] += quantity
            j += 1
        i += 1
    df_weekly_pizzas["mean"] = df_weekly_pizzas.iloc[:,1:52].sum(axis=1)/51
    # We add up to 51 weeks because the last one isn't complete
    df_weekly_pizzas["optimal"] = 0
    values = range(-8, 0)   # Deviations from the mean.
    for i in range(df_weekly_pizzas.shape[0]):
        profits = {}   
        # A dicitonary in which keys are possible deviations form the mean (-8 to +3) and values are profit for each deviation
        for value in values:
            profits[value] = 0
            mean = int(df_weekly_pizzas.loc[i, "mean"]) + value
            for j in range(1, 52):
                difference = mean - df_weekly_pizzas.iloc[i, j]
                if difference < 0:
                    profits[value] -= abs(difference)*df_prices.loc[df_weekly_pizzas.iloc[i, 0], "price"] * 0.15
                    # Supposing we have a 15% profit for each sold pizza
                elif difference > 0: 
                    profits[value] -= abs(difference)*df_prices.loc[df_weekly_pizzas.iloc[i, 0], "price"] * 0.85
                    # Because you spent a 85% of the final price but didn't sell it
        # Maximum profit and optimal deviations from the mean (will be updated in the second loop
        maximum = -100000   
        optimal = 0    
        for key, profit in profits.items():
            if maximum != max(maximum, profit):
                maximum, optimal = profit, key
        df_weekly_pizzas.loc[i, "optimal"] = int(mean) + optimal
        # Column in which we select the optimal number of pizzas to make in a week.
    return df_weekly_pizzas

def obtain_optimal(df_weekly_pizzas, pizza_ingredients, ingredients):
    """
    Iterate through the column optimal of df_weekly_pizzas to
    work out the aumount of each ingredient we need to be able to sell
    the number of pizzas previously calculated
    """
    for index, row in df_weekly_pizzas.iterrows():
        pizza = row["pizza"]
        quantity = row["optimal"]
        for ingredient in pizza_ingredients[pizza].split(", "):
            ingredients[ingredient] += quantity
    return ingredients

def show_strategy(optimal_ingredients):
    """
    Print our final results to see the quantity of each ingredient
    """
    spaces = 35
    print("Ingredients:" + " "*(spaces - len("Ingredients") - 1) + "Quantity:")
    print("-"*40)
    for key, value in optimal_ingredients.items():
        print(key + " "*(spaces - len(key)) + str(value))

def create_csv(optimal_ingredients):
    """
    Create a new dictionary to transform our data into 
    a DataFrame so it can be displayes as a csv
    """
    ingredients = {"Ingredients": [], "Quantity": []}
    for key, value in optimal_ingredients.items():
        ingredients["Ingredients"].append(key)
        ingredients["Quantity"].append(value)
    df = pd.DataFrame(ingredients)
    df.to_csv("optimal_ingredients.csv")

if __name__ == "__main__":
    df_orders = pd.read_csv("orders.csv")
    df_order_details = pd.read_csv("order_details.csv")
    df_pizzas = pd.read_csv("pizzas.csv")
    df_pizza_types = pd.read_csv("pizza_types.csv", encoding="latin1")
    

    pizza_ingredients = create_pizza_ingredients(df_pizza_types)
    ingredients = create_ingredients(pizza_ingredients)

    df_prices = obtain_prices(df_pizzas)
    df_weekly_pizzas = create_weekly_pizzas(df_orders, df_order_details, df_prices)

    optimal_ingredients = obtain_optimal(df_weekly_pizzas, pizza_ingredients, ingredients)

    show_strategy(optimal_ingredients)
    create_csv(optimal_ingredients)