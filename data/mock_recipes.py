
MOCK_RECIPE_SIMPLE_A = {
            "_id": "air_water_test",
            "format": "simple",
            "version": "0.0.1",
            "operations": [
                            [0, "air_temperature", 24],
                            [0, "water_temperature", 22],
                            [30, "air_temperature", 24],  # Lesson Learned interpret_simple_recipe calculates the end time by the last time in the list
                            [30, "water_temperature", 22]
                          ]
            }

MOCK_RECIPE_SIMPLE_B = {
  "_id": "test",
  "version": "6.1.7",
  "format": "simple",
  "operations": [
    # recipe_start
    [ 0, "one", 1 ],
    [ 0, "two", 2 ],
    [ 0, "three", 3 ],
    [ 60, "four", 4 ],
    [ 60, "five", 5 ],
    [ 120, "six", 6 ],
    [ 120, "seven", 7 ],
    [ 180, "eight", 8 ],
    # recipe_end
  ]
}

MOCK_RECIPE_FLEXFORMAT_A = {
    "_id": "example_recipe_flexformat",
    "author": "John Doe",
    "certified_by": [
        "SuperSmartScientist"
    ],
    "date_created": "2017-02-08",
    "downloads": 10000,
    "format": "flexformat",
    "optimization": [
        "general purpose"
    ],
    "phases": [
        {
            "cycles": 14,
            "name": "early",
            "step": {
                "air_temperature": [
                    {
                        "end_time": 7,
                        "start_time": 0,
                        "value": 22
                    },
                    {
                        "end_time": 18,
                        "start_time": 7,
                        "value": 25
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 23
                    }
                ],
                "light_intensity_blue": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 0
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 1
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 0
                    }
                ],
                "light_intensity_red": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 1
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 1
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 0
                    }
                ],
                "nutrient_flora_duo_a": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 5
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 2
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 5
                    }
                ],
                "nutrient_flora_duo_b": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 2
                    }
                ]
            },
            "time_units": "hours",
            "variable_units": {
                "air_temperature": "Celcius",
                "light_illuminance": "percent_relative",
                "nutrient_flora_duo_a": "ml",
                "nutrient_flora_duo_b": "ml"
            }
        },
        {
            "cycles": 20,
            "name": "middle",
            "step": {
                "air_temperature": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 20
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 23
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 19
                    }
                ],
                "light_illuminance": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 4
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 3
                    }
                ],
                "nutrient_flora_duo_a": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 5
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 2
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 5
                    }
                ],
                "nutrient_flora_duo_b": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 2
                    }
                ]
            },
            "time_units": "hours",
            "variable_units": {
                "air_temperature": "Celcius",
                "light_illuminance": "percent_relative",
                "nutrient_flora_duo_a": "ml",
                "nutrient_flora_duo_b": "ml"
            }
        },
        {
            "cycles": 7,
            "name": "late",
            "step": {
                "air_temperature": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 20
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 23
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 19
                    }
                ],
                "light_illuminance": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 4
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 3
                    }
                ],
                "nutrient_flora_duo_a": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 5
                    },
                    {
                        "end_time": 18,
                        "start_time": 6,
                        "value": 2
                    },
                    {
                        "end_time": 24,
                        "start_time": 18,
                        "value": 5
                    }
                ],
                "nutrient_flora_duo_b": [
                    {
                        "end_time": 6,
                        "start_time": 0,
                        "value": 2
                    }
                ]
            },
            "time_units": "hours",
            "variable_units": {
                "air_temperature": "Celcius",
                "light_illuminance": "percent_relative",
                "nutrient_flora_duo_a": "ml",
                "nutrient_flora_duo_b": "ml"
            }
        }
    ],
    "plant_type": [
        "lettuce",
        "green"
    ],
    "rating": 20,
    "seeds": [
        "green_lettuce_seed",
        "romaine_lettuce_seed"
    ],
    "version": "1.0"
}
