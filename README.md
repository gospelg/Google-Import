# Google-Import
Updates Google Domain Users 

********************************************************************************************************************************

PART 1
Themes


Section 1.1: History

In the days of yore, there was a powershell script. This script compared a csv gotten from Skyward (by NEFEC) to a csv outputted by GAM. The csv from Skyward contained all of the students currently enrolled in union county schools, and many bits of information about them, like name, email, student id etc. This script would find the differences, and update our google active directory as needed. This script was bloated, hard to read, and generally ineffectual. 

One day, I noticed that it was not working as expected. Another day down the road, it started to not work at all. I did some troubleshooting, and got it working, but it was horribly slow and still did not work the way it should have. I was faced with a crossroads, either debug this elephant of a script, or write a new one. Well, I chose the latter.


Section 1.2: Some General Ideas

I wrote the script in python. You may not know much about python, but that is ok. Python is optimized for humans, and is very readable and intuitive. Also, I believed in python I could drastically reduce the overall length of the script, while adding more features. I was successful in shortening the script while still making it more functional and robust. 

When I took this job, the only thing that truly scared me was the old google import powershell script, referenced in the History section. Python is one of my idiosynchrasies, and most networking guys probably won't recognize it. However, I don't want this script to scare you. That is the purpose of this readme, namely, to demistify this mission critical piece of software. 

I will do my best to describe its inner workings in painstaking, yet clear and easy to understand detail. In this case, if you ever need to debug it, or add to it, subtract from it, whatever, you will be well equipped to do so.

I strived to make this read me friendly to those with little or no programming experience, since I've been there. As such, if you know a basic amount of programming jargon, this read me will come across as somewhat insulting. I do not want to insult your intelligence, but make this sucker super easy to get you head around. If you know the basics, then you can skim over the more basic parts, but for the tried and true networking guy who has never fooled around with code, I want this to be understandable to you as well. 

There are some general things to look out for in this script. The main thing, is that this script has alot of really long strings. We have to send alot of commands to GAM, which will often include a long file path a command and several arguements. This manifests itself as alot of really long strings. It's generally not pythonic to have really long horizontal lines of code, because it's ugly and a pain to read, so I've split alot of those strings over multiple lines for comfort. For example:

	
	gam_sheet = "C:\Users\backend\Desktop\gam-64\gam.exe print users suspended custom UCSDstudent > C:\users\backend\deskt\google_import\student_id.csv"
	
This is a super long string that is used. In python, one of the things you can do is continue things over several lines if they are in parentheses. So to define a variable as a string, you don't need parentheses but if you add them you can break the string up, like this:

	gam_sheet = (r"C:\Users\backend\Desktop\gam-64\gam.exe "
                     r"print users suspended custom UCSDstudent "
                     r"> C:\users\backend\desktop\google_import\student_id.csv")
		     
This is much nicer. Another somewhat strange convention in this script, is the way I've done string formatting. An example that you would normally see in python looks like this:

	some_string = "The {0} jumped over the {1}".format("cow", "moon")
These means that some_string = The cow jumped over the moon. The syntax I use mostly, is to put it in parentheses and break it up over two lines, with .format() on the second. Like this:

	some_string = ("The {0} jumped over the {1}"
	               .format("cow", "moon"))
		
This helps the code stay justified and neat, because having the .format() on the first line would put me over my horizontal limit in some places. I have it set up to where no line is longer than 99 characters. To help with this, alot of my gam commands are defined as variables first. Instead of using call(C:\somewhere\somewhere\gam.exe do stuff) I will put everything in those parantheses to a variable before hand, and then pass it to call(). So, instead we have call(variable). This is a little bit cleaner and also helps to keep those lines short. In addition to the actual string of stuff we send to call, you will notice there is another arguement given, which is shell=True. This means that everything in the call function will be executed by windows and not python. It allows us to call an exe and also send arguements to that exe at the same time. In our case, start gam.exe and at the same time give it commands.
		      
		


Section 1.3: Layout

The script is laid out in a pretty straightforward manner. If you are familiar with python, most scripts look similar. At the top, we import the stuff we need. Python has a bunch of handy tools called modules, which are these python files that have different premade functions and stuff. You can make your own modules, but for this script we just need a few stock ones. They are pretty self explanatory, like import csv, which imports tools for reading csv files. Also, in this top section I set up my log file. The logging in this script is thorough, but straitforward. There is logging.info() and logging.warning(). Anything you put in the parentheses will be sent to the log, either as info or as a warning. 

I also set a variable for the date, but it's literally only used for setting the name of the log file.

********************************************************************************************************************************

PART 2
Functions


Section 2.1: The Main Function

The roadmap for the whole script is the main() function. 

	def main ():

		root_dir = r'C:\users\backend\desktop\google_import'
		date = time.strftime("%m_%d_%Y")
		logging.basicConfig(filename='{0}\logs\log{1}.log'
							.format(root_dir, date), level=logging.DEBUG)

		#makes gam print out a csv of all the users in GAD, with all fields to a csv
		gam_sheet = (r"C:\Users\backend\Desktop\gam-64\gam.exe "
					 r"print users suspended custom UCSDstudent "
					 r"> C:\users\backend\desktop\google_import\student_id.csv")
		call(gam_sheet, shell=True)

		#assign files to variables
		logins = list_maker((r"{0}\sftp\GoogleLogins.csv").format(root_dir))
		home_logins = list_maker((r"{0}\sftp\GoogleLoginsHomeSchool.csv").format(root_dir))
		gam_output = tuple(list_maker((r"{0}\student_id.csv").format(root_dir)))

		logins = combiner(logins, home_logins)

		users_add = new_students(logins, gam_output)
		users_remove = gone_students(logins, gam_output)

		import_students(users_add)
		remove_students(users_remove)
		update_passwords(logins)
  
That is the main() function. This is like the master function, and calls all the other functions in the script. First thing it does is get GAM to spit out a csv. I use the call() function in python, which is imported from the subprocess module. call() allows me to pass a string to command prompt in windows. So, whatever is in the parantheses of call() will go to command prompt as if you just opened command prompt and typed it in. 
  
The first thing we do here, is define a variable called root_dir, which we will use a few times. This is our google_import folder, where all the magic happens. I also define the time in a format I like, and set up a log file. The leve=logging.DEBUG means that pretty much all logging levels get sent to the log, from info all the way up.
  
This GAM command makes a csv with ALL users in the google domain, with the suspended field, our custom schema field, which is the student ID. Feel free to navigate to the path listed in the command, open up the csv and have a look. The > is a pipe in GAM's syntax, in this case just where to save the file.
  
Next thing it does is wait 15 seconds (with the sleep() function). This is to give GAM enough time to generate that csv before the script starts doing stuff.
  
After this, the script loads the content of the csv files to variables. This way, we only need to open them in python once, and then they are stored in memory. It makes the script run faster this way, and also makes calling up the data easier. It uses the list_maker() function to load the data from the csv to a list. I will go over this important function later. 
  
Nefec gives us two csv's, one for regular students and one for homeschool students. For ease of use, we will combine these. You will see that the variable logins is redefined, as the output of the combiner() function. This does exactly what you might expect, it combines the data from both lists. Will go over that function in detail later. 
  
The next little bit is pretty straight forward. We want to further refine our data, and get a list of students we need to add, and a list we need to remove. After that, we want to actually add them, and remove them. So I have the users_add and users_remove variables, which are the outputs of new_students() function and gone_students() function, respectively. Now that those functions have ran, we now know which students need to be added and removed. the import_students() funtion and remove_students() function actually do that. They issue the GAM commands to make changes in the google directory. 
  
  
  Section 2.2: The list_maker Function
  
  This is the function that converts the data in the csv's to a python list. Actually, a list of lists.
  
		def list_maker(file_path):
    		with open(file_path, 'r') as f:
        		reader = csv.reader(f, delimiter=',')
        		next(reader, None)
        		new_list = list(reader)
        		return new_list
      
So, the only arguement it takes is file_path, which should be a string with the path to the csv you want to load (notice this in the first few lines of the main function). Python uses what's called a context manager (with) which opens and closes the file automagically. So you don't have to manually close it, which rocks. This one is super straight forward. Few points of interest:
     1. the next() function. This is so that python will skip the very first row in the csv. We don't really need the headers, and they will mess stuff up for us anyway.
     2. reader will go through the csv line by line. Notice the logic, new_list is a list of all the lines in reader. So, each line in the csv is a list of strings, and new_list is a list of all those lists. A bit of a mouthful, yes. So new_list is one object, containing all the lines of the csv, with each line as its own seperate list inside of new_list. Got it? 
  
In python, lists are mutable. This means we can change them, and in our case add to them later (in the combiner function). So for now, we want our csv's turned into big lists that we can do stuff with them. 

Section 2.3: The combiner Function
    
This function turns two lists into one. Technically, it takes two list of lists, and adds all the lists from one to the end of the other. In our case, going back to the main function we will find this line:
    
    home_logins = list_maker((r"{0}\sftp\GoogleLoginsHomeSchool.csv").format(root_dir))
    
Given what we know about the list_maker function, home_logins will be a list of lists, where each list is a line of the GoogleLoginsHomeSchool.csv The function itself is easy as pie
    
    def combiner(list1, list2):
	for item in list2:
		list1.append(item)
	return tuple(list1)
    
For each item in list2, add it to the end of list1. Return list1 as a tuple. Boom. So list2 should be the home_logins, and it just adds those to list one, logins, and turns the whole thing into a tuple and spits it out. Tuples are immutable in python, and I have found that python can search tuples better than lists with if in or not in statements.
    
Section 2.4: The new_students Function
    
The new students function compares the data gotten from NEFEC with the data gotten from google to find students that need to be added.

	def new_students(nefec, google):
    	users_add = {"new":[], "unsuspend": []}
    	for item in nefec:
        	for x in google:
            	if item[11] == x[3] and x[1] == "False":
               		break
           	 	if item[11] == x[3] and x[1] == "True":
                	users_add["unsuspend"].append(item)
                	break
        else:
            users_add["new"].append(item)
    return users_add
    
So, this takes two arguements, which should be logins and gam_output (as defined in the main function). We are going to create a dictionary, which is a sort of data construct that has a key:value structure. So the keys in this dictionary are "new" and "unsuspend". This way, we can seperate the truly new users from those who just need their account switched on. The value that goes with each key is a list, which in our case will end up as a list of lists. On to the meat of the function:
    
We've got a nested for loop here, and it works like this. For item in nefec, so for each list (read that as set of student data): then it goes for x in google, which is the same thing (for each set of student data in google, what began as each line in the gam_output csv). So it's going to take each thing in NEFEC, and for each thing in nefec search each thing in google. We then have a few if statements. The first, checks to see if the student ID of the current item in nefec can be found in the google object. If it is, and x[1] is equal to false (x[1] here is just an index of x, which is a line in the google object, in our case this translates to the suspended field.) then we get a break. So this means, as soon as python sees that the student ID is in both lists, and the user is not suspended, it stops and moves on to the next thing in NEFEC. 
   
The second if statement is very similar to the first. Only, it matches if x[1] is True. This means that the user is in both lists, but is listed in the google list as being suspended. In this case, we add it to our dictionary under the unsuspend key. At this point there is also a break, and it will stop looping and move on to the next item in NEFEC.
   
This last bit, is an else statement. But notice the indent! This else statement does not apply to the if statements, but to the for loop itself. Basically, in python it works like this: You can make a for loop, and if the loop goes all the way through without hitting a break, it will move on to the else statement you put with it. In our case, breaks only happen if it matches an if statement. If it doesn't, it means that the item in the nefec object is nowhere to be found in the google object. This is a student who needs to be created, and as such, under our else statement we add this item to the "new" key in our dictionary.
   
Lastly, we return the dictionary that has all the students who need to be added or unsuspended.
   
Section 2.5: The gone_students Function
    
This function is quite similar to new students, only it is looking for students that are no longer enrolled.
    
    def gone_students(nefec, google):
	deactivate = []
	for student in google:
	    if student[3] != "" and student[1] == "False":
		for item in nefec:
			if student[3] in item[11]: 
			    break
			else:
		            deactivate.append(student[0])
				
	return deactivate
    
This one is much simpler though. We see the same sort of nested for loop, with an else statement hooked to it. However, our data will be more straightforward and we can work with a regular old list instead of having to make a dictionary. The logic is also reversed. Instead of going through the things in the NEFEC object, and checking if they are in the google object, we will go through things in the google object and check to see if they are in the NEFEC object. 
    
First I define a list that will contain the emails of students who need to be deactivated. Then we set up a for loop, for each student in google. Then there is an if statement to determine if we should continue.
  
 THIS IS UBER SUPER IMOPRTANT!!!!! PAY ATTENTION TO THIS IF STATEMENT OR YOU WILL BREAK THE ENTIRE GOOGLE DOMAIN!!!!!!!
  
Sorry for screaming at you, but this is insanely important. This if statment 2 conditions: The first- student[0] != "" 
Student[0] is the student ID field in the google csv. this statment in plain english reads, if the student id field is not blank. The google csv contains very single user in the entire domain, including staff. Having this condition means that the function will automatically skip all staff accounts. If it didn't, this script would disable every single account without a student ID, which is really bad. The other condition, is student[1] == "False", or the suspended field is equal to false. We don't need to suspend accounts that are already suspended.
  
So, from the top, we loop through every item in the google object, and test them against two conditions in our if statement. If they do not meet the conditions, python moves on to the next item in the google object. If the item does meet the two conditions, it moves on to another for loop.
  
This for loop will go through every item in the nefec object, and compare it to the current item in the google object with an if statement. Again, we are looking at the student ID fields in both objects. So, if the student ID is in both, then break and move on. IF it goes through the whole loop, and does not find the student ID in the NEFEC object, we know we have an account in google for a student who is no longer enrolled. So in the else statement, we add it to the deactivate list. GAM only needs the email address to deactivate an account, so that's all we will add to the deactivate list. Lastly, we return this list.
  
Section 2.6: The import_students Function
  
This function takes the results of the new_students function, and does stuff with it.
  
	def import_students(students):
            for kid in students["new"]:
       		i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        	i.add_user()
                i.move_user()
            for kid in students["unsuspend"]:
                i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        	i.unsuspend()
        	i.move_user()	
        
This is mostly pretty simple. It just takes dictionary that new_students made, and then instantiates everything in the dictionary. Instantiate means to make an instance of, which will make more sense in Section 3 when I go over the student class. So, there are to simple for loops. One is for everything under the "new" key in the dictionary. It creates an instance of the student class for each of those things, and then calls the add_user() and move_user() functions that exist in the student class.
The other for loop does the same exact thing, except calling unsuspend() instead of add_user().
        
Section 2.7: The remove_user Function
      
This one takes the results of the gone_students function, and suspends accounts for the students who are no longer enrolled.
        
	def remove_students(students):
    gam = r"C:\Users\backend\Desktop\gam-64\gam.exe"
    for kid in students:
        try:
            gam_input = ("{0} update user {1} suspended on"
                         .format(gam, kid))
            call(gam_input, shell=True)
            #moves them to suspended users ou
            gam_input1 = ('{0} update org "/Suspended Users" add users {1}'
                          .format(gam, kid))
            call(gam_input1, shell=True)
            logging.info("Sucessfully suspended user {0} and moved to suspended OU"
                         .format(kid))
        except:
            logging.warning("Could not suspend {0} or move to suspended OU"
                            .format(kid))
            
If you remember, students should be a list of emails. Here we use call() to send a command to command prompt. This is in a for loop, so it will do this for each thing in the students object (which translates to each email). I use some simple string formatting to replace the email with whatever one we are on during the for loop. The gam command will just turn suspended on. The next call then moves the user to the suspended users ou. Easy.
     
Here we have a try: statement. This basically is means, do this, but if you try and get an error, then do whatever is in the except: statement instead. This helps with logging, as you can see, we can log that it was successful if it was, or log that it failed if it failed.
     
   ********************************************************************************************************************************
     
PART 3
THE CLASS
            
     
Section 3.1: What it is
    
So classes are important concepts in object oriented p
