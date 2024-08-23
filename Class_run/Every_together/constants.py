obj_list = ['cart', 'basket', 'exit', 
            'milk', 'chocolate_milk', 'strawberry_milk', 'apples',
            'oranges', 'banana', 'strawberry', 'raspberry',
            'sausage', 'steak', 'chicken', 'ham',
            'brie_cheese', 'swiss_cheese', 'cheese_wheel',
            'garlic', 'leek', 'red_bell_pepper', 'carrot', 'lettuce',
            'avocado', 'broccoli', 'cucumber', 'yellow_bell_pepper', 'onion', 
            'prepared_foods', 'fresh_fish', 
            # TODO: ADD RETURNS     
            'checkout'] 


cart_obj_pos_dict = {
    'basketreturns': [3.5, 17.5], 
    'cartreturns': [1.5, 17.5],    
    'milk': [6, 3.5], 
    'chocolate_milk': [10, 3.5],
    'strawberry_milk': [14, 3.5], 

    'apples': [6, 7.5], 
    'oranges': [8, 7.5],
    'banana': [10, 7.5],
    'strawberry': [12, 7.5],
    'raspberry': [14, 7.5], 

    'sausage': [6, 11.5], 
    'steak': [8, 11.5], 
    'chicken': [12, 11.5], 
    'ham': [14, 11.5],

    'brie_cheese': [6, 15.5],
    'swiss_cheese': [8, 15.5], 
    'cheese_wheel': [10, 15.5], 

    'garlic': [6, 19.5], 
    'leek': [8, 19.5], 
    'red_bell_pepper': [10, 19.5], 
    'carrot': [12, 19.5], 
    'lettuce': [14, 19.5], 
    'broccoli': [8, 23.5],
    'cucumber': [10, 23.5], 
    'yellow_bell_pepper': [12, 23.5], 
    'onion': [14, 23.5], 
    'avocado': [6, 23.5], 

    'prepared_foods': [16.5, 5],
    'fresh_fish': [16.5, 11],

    'registers': [4.5, 11.5],
    'exit': [0, 3.2],
}


obj_pos_dict = {
    'cart': [2.4, 17.6],
    'basket': [3.4, 17.6],
    'exit': [0, 3.2],

    # milk
    'milk': [7.2, 3.0],
    'chocolate_milk': [11.4, 3.0],
    'strawberry_milk': [14.4, 3.0], 

    # fruit
    'apples': [6.4, 4.6],
    'oranges': [8.4, 4.6],
    'banana': [10.4, 4.6],
    'strawberry': [12.4, 4.6],
    'raspberry': [14.4, 4.6],

    # meat
    'sausage': [6.2, 8.6],
    'steak': [9.2, 8.6],
    'chicken': [12.2, 8.6],
    'ham': [14.8, 8.6], 

    # cheese
    'brie_cheese': [6.4, 12.6],
    'swiss_cheese': [8.4, 12.6],
    'cheese_wheel': [12.4, 12.6], 

    # veggie 
    'garlic': [6.2, 16.6], 
    'leek': [8.4, 16.6], 
    'red_bell_pepper': [10.2, 16.6], 
    'carrot': [12.4, 16.6],
    'lettuce': [14.2, 16.6], 

    # something else 
    'avocado': [6.2, 20.6],
    'broccoli': [8.4, 20.6],
    'cucumber': [10.4, 20.6],
    'yellow_bell_pepper': [12.4, 20.6], 
    'onion': [14.4, 20.6], 

    'prepared_foods': [17.2, 5.8], 
    'fresh_fish': [17.2, 11.2],
    'checkout': [1, 3.6]
} 


horizontal_blocks = [
    # checkouts
    # [[0, 12.2], [3.2, 12.2]],
    # [[0, 8.8], [3.2, 8.8]],
    # [[0, 7.2], [3.2, 7.2]],
    # [[0, 3.8], [3.2, 3.8]], 
     [[0, 12.2], [4, 12.2]],
    [[0, 8.8], [4, 8.8]],
    [[0, 7.2], [4, 7.2]],
    [[0, 3.8], [4, 3.8]], 

    # shelves
    [[0, 3], [19, 3]],
    [[4, 4.6], [16, 4.6]],
    [[4, 7], [16, 7]],
    [[4, 8.6], [16, 8.6]],
    [[4, 11], [16, 11]],
    [[4, 12.6], [16, 12.6]],
    [[4, 15], [16, 15]],
    [[4, 16.6], [16, 16.6]],
    [[4, 19], [16, 19]],
    [[4, 20.6], [16, 20.6]],
    [[4, 23], [16, 23]],

    # something else
    [[17.2, 13.2], [18.8, 13.2]],
    [[17.2, 10.2], [18.8, 10.2]],
    [[17.2, 7.2], [18.8, 7.2]],
    [[17.2, 4.2], [18.8, 4.2]], 
     
    # walls 
    [[0, 2.2], [18.8, 2.2]],
    [[0, 24.2], [18.8, 24.2]],

    # carts
    # [[0, 17.8], [3.8, 17.8]],
    [[0, 17.4], [3.8, 17.4]],
]

vertical_blocks = [
    # walls 
    [[0, 2.2], [0, 2.8]],
    [[0, 7.8], [0, 8.8]],
    [[0, 12.2], [0, 17.8]], 
    # 
    [[17, 1.2], [17, 24.4]],


    # checkouts 
    # [[3.8, 3.8], [3.8, 7.2]],
    # [[3.8, 9.2], [3.8, 12.2]], 
    [[4, 3.8], [4, 7.2]],
    [[4, 9.2], [4, 12.2]], 

    # shelves
    [[4, 4.5], [4, 7.1]],
    [[4, 8.5], [4, 11.1]],
    [[4, 12.5], [4, 15.1]],
    [[4, 16.5], [4, 19.1]],
    [[4, 20.5], [4, 23.1]],

    [[16, 4.5], [16, 7.1]],
    [[16, 8.5], [16, 11.1]],
    [[16, 12.5], [16, 15.1]],
    [[16, 16.5], [16, 19.1]],
    [[16, 20.5], [16, 23.1]], 

    # something else
    [[17.4, 4.2], [17.4, 7.2]], 
    [[17.4, 10.2], [17.4, 13.2]],

    # carts
    # [[4.2, 17.8], [4.2, 24.2]],
    [[4.2, 17.4], [4.2, 24.2]],
] 

max_x, max_y = 20, 25