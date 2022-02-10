import re

upperRegex = re.compile(r'[A-Z]')
lowerRegex = re.compile(r'[a-z]')
numberRegex = re.compile(r'\d')
specialRegex = re.compile(r'\W')  # \W

pswd = 'Password1234'

# # check for at least 1 capital letter
# caps = ['ABCDEFGHIJKLMNOPQRSTUVWXYZ']

# # check for at least 1 lower case letter
# lower = ['abcdefghijklmnopqrstuvwxyz']

# # check for at least 1 digit
# nums = ['0123456789']

# # check for 1 non alpha numeric character
# non = ['~`!@#$%^&*()-+={}|:;<>,.?/\\\'\"']

if(upperRegex.search(pswd) == None):
    print("The string does not contain an uppercase letter")
else:
    print("The string contains an uppercase letter")

if(lowerRegex.search(pswd) == None):
    print("The string does not contain a lowercase letter")
else:
    print("The string contains a lowercase letter")

if(numberRegex.search(pswd) == None):
    print("The string does not contain a number")
else:
    print("The string contains a number")

if(specialRegex.search(pswd) == None):
    print("The string does not contain a special character")
else:
    print("The string contains a special character")

# # Python program to check if a string
# # contains any special character

# import re

# # Getting string input from the user
# myStr =  input('Enter the string : ')

# # Checking if a string contains any special character
# regularExp = re.compile('[@_!#$%^&*()<>?/\|}{~:]')

# # Printing values
# print("Entered String is ", myStr)
# if(regularExp.search(myStr) == None):
#     print("The string does not contain special character(s)")
# else:
#     print("The string contains special character(s)")

