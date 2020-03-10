
# DESCRIPTION --> Getting buy_share_price, sell_share_price & sell_share_price in the event of a 100% gain


def finding_value_from_exact_date(df, exact_date):  # Used in the share price function within the class

    date = ""   # Need to write this as I had to come up with an idea to check if there was actually a value (taken from the date) in the dataframe

    for i in range(len(df)):

        if df['date'].iloc[i] == exact_date:

            date = df['date'].iloc[i]
            #index = i
            return df['close'].iloc[i]

        # Can't just write an else statement, as it would otherwise return 0 straight after the first loop
            '''
            else: 
                return 0
            '''      


    if date == "":  # This is referring back to the empty string variable, date, created at the start of the function 
        return 0    # Used to return 0, in the event that no data for a specific date is present (eg in the even that the company had not gone public back then)
        



def finding_index_from_exact_date(df, exact_date):  # Used in the share price function within the class

    for i in range(len(df)):

        if exact_date in df['date'].iloc[i]:

            date = df['date'].iloc[i]
            index = i
            return index    # Choosing to return the index instead of value to save into a new variable within the funciton (within the class)





class analysing_share_price(object):
    
    def __init__(self, data_share_price, goal_roi, buy_share_price_date, sell_share_price_date):
        
        self.data_share_price = data_share_price
        self.goal_roi = goal_roi
        self.buy_share_price_date = buy_share_price_date
        self.sell_share_price_date = sell_share_price_date
    

    def buy_share_price(self):

        self.buy_share_price = finding_value_from_exact_date(self.data_share_price, self.buy_share_price_date)     # Using function written outside of class to get share price from chosen buy date
        self.buy_share_price = float(self.buy_share_price)    # Convert buy_share_price into an integer
        return self.buy_share_price

    def sell_share_price_end_of_period(self):

        self.sell_share_price_end_of_period = finding_value_from_exact_date(self.data_share_price, self.sell_share_price_date)     # Using function written outside of class to get share price from chosen sell date
        self.sell_share_price_end_of_period = float(self.sell_share_price_end_of_period)    # Convert sell_share_price_end_of_period into an integer
        return self.sell_share_price_end_of_period

        #print("The buy_share_price at the beginning of the period is " + str(self.buy_share_price))
        

    '''
    # REDUNDANT NOW --> 
        # This code was previously written when I wanted to find out the maximum sell price possible in between 3 years
        # But this is now redundant as I have decided to focus on working on my investment criteria
        # Instead of testing whether I should allow for a greater (eg 120% gain) instead of 100% gain
    def max_sell_share_price(self):

        # This iteration is to find the maximum sell price possible, over the period of 3 years
        for i in range(self.no_of_indexes_in_between):

            if self.data_share_price["close"].iloc[i+self.buy_date_index] > self.max_sell_price_possible:   # Had to do (i + self.buy_date_index) to start analysing share price from the buy data
                
                self.max_sell_price_possible = self.data_share_price["close"].iloc[i+self.buy_date_index]
                self.max_sell_price_possible = float(self.max_sell_price_possible)
    '''


    def share_price_of_100_gain(self):
        
        self.buy_date_index = finding_index_from_exact_date(self.data_share_price, self.buy_share_price_date)   # Getting the index no of buy_share_price in the dataframe
        self.sell_date_index = finding_index_from_exact_date(self.data_share_price, self.sell_share_price_date)     # Getting the index no of sell_share_price in the dataframe

        # Calculating how many indexes there are in between the buy_share_price and sell_share_price
        self.no_of_indexes_in_between = self.sell_date_index - self.buy_date_index  


        self.sell_date_of_100_gain = ""   # Need to write this as I had to come up with an idea to check if there was actually a value (taken from the date) in the dataframe

        for i in range(self.no_of_indexes_in_between):

            if self.data_share_price["close"].iloc[i+self.buy_date_index] > (self.goal_roi * self.buy_share_price):     
            # If selected share price is larger than 100% gain (aka 2 * buy_share_price)

                self.sell_date_of_100_gain = self.data_share_price["date"].iloc[i+self.buy_date_index]  # Get date when selling at 100% gain from buy_share_price
                self.sell_share_price_of_100_gain = self.data_share_price["close"].iloc[i+self.buy_date_index]  # Get sell share price at 100% gain
                self.sell_share_price_of_100_gain = float(self.sell_share_price_of_100_gain)    # Converting string into an integer

                return self.sell_share_price_of_100_gain    # Asign value (of 100% gain from buy_share_price) to variable
    
        
        if self.sell_date_of_100_gain == "":  # This is referring back to the empty string variable, date, created at the start of the function 

            self.sell_share_price_of_100_gain = 0

            return self.sell_share_price_of_100_gain   # Writing to return 0, in the event that no data for a specific date is present (eg in the even that the company had not gone public back then)

        
        #print("(If applicable) the sell_share_price at 100% gain is " + str(self.sell_share_price_of_100_gain))
    


    def final_sell_share_price(self):

        # Comparing the sell_share_price at the end of 3 years vs sell_share_price of 100% gain
        if self.sell_share_price_end_of_period > self.sell_share_price_of_100_gain:

            self.final_sell_share_price = self.sell_share_price_end_of_period
            #self.final_sell_share_price_date = self.sell_share_price_date  # Getting the date of final_sell_share_price
        

        elif self.sell_share_price_of_100_gain > self.sell_share_price_end_of_period:

            self.final_sell_share_price = self.sell_share_price_of_100_gain
            #self.final_sell_share_price_date = self.sell_date_of_100_gain  # Getting the date of final_sell_share_price

        return self.final_sell_share_price  # Asigning value of final_sell_share_price to a variable



    def date_of_final_sell_share_price(self):
        
        # Comparing the sell_share_price at the end of 3 years vs sell_share_price of 100% gain
        if self.sell_share_price_end_of_period > self.sell_share_price_of_100_gain:      

            self.final_sell_share_price_date = self.sell_share_price_date   # Getting the date of final_sell_share_price
        

        elif self.sell_share_price_of_100_gain > self.sell_share_price_end_of_period:

            self.final_sell_share_price_date = self.sell_date_of_100_gain   # Getting the date of final_sell_share_price

        return self.final_sell_share_price_date     # Asigning value of final_sell_share_price_date to a variable









'''
# Only use this to test the analysing_json_files class

path_share_price = f"/Users/jin/Desktop/download/f_statements/share-prices/AAPL.json"

df_share_price = open(path_share_price, 'r')     # Open the file
        
df_share_price = df_share_price.read()  # This converts the file into a string (aka an object)
df_share_price = json.loads(df_share_price)     # This converts the object into a dictionary
        
df_share_price = pd.DataFrame.from_dict(df_share_price['historical'])   # Lastly, this converts the file into a dataframe




calling_class = analysing_share_price(df_share_price, 2, "2017-02-01", "2019-02-01")

# Still need to call the functions with the class to get any outputs
calling_class.buy_share_price()
calling_class.sell_share_price_end_of_period()
calling_class.share_price_of_100_gain()

calling_class.final_sell_share_price()
t = calling_class.date_of_final_sell_share_price()
print(t)
'''