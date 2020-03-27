# DESCRIPTION --> Calculating rate of accuracy of investing strategy




def calculate_rate_of_accuracy(array_stocks_pass_criteria, array_stocks_share_price_increase):

    if len(array_stocks_pass_criteria) < 1:
        return 'There is no rate of accuracy as 0 stock pass your investment criteria.'

    else:

        rate_of_accuracy = len(array_stocks_share_price_increase)/len(array_stocks_pass_criteria)
        rate_of_accuracy = round(rate_of_accuracy, 2)   # To round rate of accuracy to 2 dp

        return 'The rate of accuracy of this investment program is ' + str(rate_of_accuracy) + '%.'




# Code to test class
'''
array_one = [1,2,3]
array_two = [1]
var = calculate_rate_of_accuracy(array_one, array_two)

print(var)
'''