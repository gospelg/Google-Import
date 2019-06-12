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

I strived to make this read me friendly to those with little or no programming experience, since I've been there. As such, if you know a basic amount of programming jargon, this read me will come across as somewhat insulting. I do not want to insult your intelligence, but make this sucker super easy to get your head around. If you know the basics, then you can skim over the more basic parts, but for the tried and true networking guy who has never fooled around with code, I want this to be understandable to you as well. 

There are some general things to look out for in this script. The main thing, is that this script has alot of really long strings. We have to send alot of commands to GAM, which will often include a long file path, a command, and several arguements. This manifests itself as alot of really long strings. It's generally not pythonic to have really long horizontal lines of code, because it's ugly and a pain to read, so I've split alot of those strings over multiple lines for comfort. For example:

	
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
		
This helps the code stay justified and neat, because having the .format() on the first line would put me over my horizontal limit in some places. I have it set up to where no line is longer than 99 characters. To help with this, alot of my gam commands are defined as variables first. Instead of using call(C:\somewhere\somewhere\gam.exe do stuff) I will put everything in those parantheses to a variable before hand, and then pass it to call(). So, instead we have call(variable). This is a little bit cleaner and also helps to keep those lines short. In addition to the actual string of stuff we send to call, you will notice there is another arguement given, which is shell=True. This means that everything in the call function will be executed by windows and not python. It allows us to call an exe and also send arguements to that exe at the same time. In our case, start gam.exe and at the same time give it commands. In the latest versions of the script, I have switched to Popen. Popen is a python module that allows you to interact with the OS python is executing in. It is the basis for call, but it is a little more granular. The purpose of which was to have more detailed logs for troubleshooting.
		      
		


Section 1.3: Layout

The script is laid out in a pretty straightforward manner. If you are familiar with python, most scripts look similar. At the top, we import the stuff we need. Python has a bunch of handy tools called modules, which are these python files that have different premade functions and stuff. You can make your own modules, but for this script we just need a few stock ones. They are pretty self explanatory, like import csv, which imports tools for reading csv files. Also, in this top section I set up my log file. The logging in this script is thorough, but straitforward. At the top we just import the logging module, in the main function we will actually set up the log in detail. 

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
        master_file = r"{0}\master\{1}master.txt".format(root_dir, date)

        #makes gam print out a csv of all the users in GAD, with all fields to a csv
        logging.info("Exporting users from google...")
        gam_sheet = (r"C:\Users\backend\Desktop\gam-64\gam.exe "
                     r"print users suspended custom UCSDstudent "
                     r"> C:\users\backend\desktop\google_import\student_id.csv")
        subprocess.call(gam_sheet, shell=True)

        #assign files to variables
        logging.info("Making lists...")
        logins = list_maker((r"{0}\sftp\GoogleLogins.csv").format(root_dir))
        home_logins = list_maker((r"{0}\sftp\GoogleLoginsHomeSchool.csv").format(root_dir))
        gam_output = tuple(list_maker((r"{0}\student_id.csv").format(root_dir)))

        logins = combiner(logins, home_logins)

        users_add = new_students(logins, gam_output)
        users_remove = gone_students(logins, gam_output)

        import_students(users_add, master_file)
        remove_students(users_remove, master_file)
        update_passwords(logins)
    
        logging.info("Staring batch operations...")
        gam_master(master_file)
  
That is the main() function. This is like the master function, and calls all the other functions in the script. It is the most dense function, and the only one that really does a bunch of different things. usually functions just have one function.

The first thing we do here, is define a variable called root_dir, which we will use a few times. This is our google_import folder, where all the magic happens. I also define the time in a format I like, and set up a log file. The leve=logging.DEBUG means that pretty much all logging levels get sent to the log, from info all the way up. In the actual log, it will say if something is info, warning, or error as it logs it.

Then I assign a variable called master file. This is very important. I've made a few changes in the general way this script works, but this is the biggest and most important. Before, the way the script worked was each time it had a command to pass to GAM, it just passed it. Now, it takes each command and writes it to this master file. Then, at the end of the script, it calls GAM once, and tells it to execute all the commands in this master file in batch mode. The advantages of this are several.
1. We can run GAM in multi-threaded mode, which decreased the amount of time it takes to run this script by a factor of 20.
2. We have another very useful logging function. If something goes wrong, you can open the master file (it is just a txt file) and see in verbose detail every single command the script is giving to GAM. This is immensely useful for troubleshooting.
3. This is similar to point 1, but it is much easier to just call GAM once, instead of thousands of times.

As you can see, it names the file with a date so you get a new master file every time the script runs, allowing you to go back and see what the script was doing, as usually you don't catch any issues until several days later.

Next thing it does is get GAM to spit out a csv. I use the call() function in python, which is imported from the subprocess module. call() allows me to pass a string to command prompt in windows. So, whatever is in the parantheses of call() will go to command prompt as if you just opened command prompt and typed it in. 
  
As you can see, it makes an note in the log that this is what it is doing before actually doing it. This GAM command makes a csv with ALL users in the google domain, with the suspended field, our custom schema field, which is the student ID. Feel free to navigate to the path listed in the command, open up the csv and have a look. The > is a pipe in GAM's syntax, in this case just where to save the file.

Next thing it does is wait 15 seconds (with the sleep() function). This is to give GAM enough time to generate that csv before the script starts doing stuff.
  
After this, the script loads the content of the csv files to variables. This way, we only need to open them in python once, and then they are stored in memory. It makes the script run faster this way, and also makes calling up the data easier. It uses the list_maker() function to load the data from the csv to a list. I will go over this important function later. 
The gam_output variable is a little different. You can see I use the tuple() function. Inside the tuple() function, it the actual listmaker function. This means that the output of list_maker() will be converted to a tuple. Tuples are arrays of things, which is vague, I know. Essentially, it can be an array of anything, so it has a little looser properties than say a list or a dictionary. The main reason I use a tuple here instead of a list, is because tuples are immutable. I was using a list here, and it led to some innacuraccies later on in the script, which is not important for me to go into. Just know that due to the immutable nature of tuples, the script works here.
  
Nefec gives us two csv's, one for regular students and one for homeschool students. For ease of use, we will combine these. You will see that the variable logins is redefined, as the output of the combiner() function. This does exactly what you might expect, it combines the data from both lists. Will go over that function in detail later. 
  
The next little bit is pretty straight forward. We want to further refine our data, and get a list of students we need to add, and a list we need to remove. After that, we want to actually add them, and remove them. So I have the users_add and users_remove variables, which are the outputs of new_students() function and gone_students() function, respectively. Now that those functions have ran, we now know which students need to be added and removed. the import_students() funtion and remove_students() function actually do that. These are the functions responsible for writing commands to the master file. 
  
  
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
    
For each item in list2, add it to the end of list1. Return list1 as a tuple. Boom. So list2 should be the home_logins, and it just adds those to list one, logins, and turns the whole thing into a tuple and spits it out. Tuples are immutable in python, and I have found that python can search tuples better than lists with if in or not in statements, as explained in section 2.1.
    
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
Student[0] is the student ID field in the google csv. this statment in plain english reads, if the student id field is not blank. The google csv contains every single user in the entire domain, including staff. Having this condition means that the function will automatically skip all staff accounts. If it didn't, this script would disable every single account without a student ID, which is really bad. The other condition, is student[1] == "False", or the suspended field is equal to false. We don't need to suspend accounts that are already suspended.
  
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
        
This is mostly pretty simple. It just takes dictionary that new_students made, and then instantiates everything in the dictionary. Instantiate means to make an instance of, which will make more sense in Section 3 when I go over the student class. So, there are two simple for loops. One is for everything under the "new" key in the dictionary. It creates an instance of the student class for each of those things, and then calls the add_user() and move_user() functions that exist in the student class.
The other for loop does the same exact thing, except calling unsuspend() instead of add_user().
        
Section 2.7: The remove_user Function
      
This one takes the results of the gone_students function, and suspends accounts for the students who are no longer enrolled.
        
	def remove_students(students, master_file):
            for kid in students:
                gam_input = ("gam update user {0} suspended on\n"
                             .format(kid))
                with open(master_file, 'a') as f:
                     f.write(gam_input)
                #moves them to suspended users ou
                gam_input1 = ('gam update org "/Suspended Users" add users {0}\n'
                              .format(kid))
                with open(master_file, 'a') as f:
                f.write(gam_input1)
            
If you remember, students should be a list of emails. So, for each line (email) in students, we write the gam command to suspend them to our master file. You can see this function takes the master file as an agruement, so that when this function runs we can tell it where the master file is. The first part adds the suspend command, the second part adds a command to move them to the suspended OU. So gam_input and gam_input1 are obviously the commands that will go to GAM here, and you can read over them to get familiar with the commands, should you so desire.
I use some simple string formatting to replace the email with whatever one we are on during the for loop.
     
Section 2.8: The Update_passwords() function

    def update_passwords(students):
        for kid in students:
            i = student(kid[2], kid[1], kid[0], kid[3], kid[11],
                        kid[5], kid[4], 0) #no need for the master_file atribute here
        i.change_password()

This one is simplicity defined. For every kid in the students list, create a student instance and call the change password method. Easy peasy. You will learn about this method in PART 3.
   ********************************************************************************************************************************
     
PART 3
THE CLASS
            
     
Section 3.1: What it is
    
So classes are important concepts in object oriented programming. They are often described as data blueprints. Its basically an empty framework, that you can fill with specific data for each instance. So here we have the student class, and we know that every student will have certain attributes, such as name, email, student ID, etc. Instead of programming each student with all this data (that would take so much code, it wouldn't even be humanly possible!) we just make a class that has these attributes set up, and fill in the data for each student as it is needed based on this blueprint. 

Not only can we attach attributes to a class, we can also attach functions. So given all the attributes, we can do certain things with this data for each instance of a student, including add them, move them, unsuspend them, and change their password. If you recall back to section 2.6 on the import_students() funtion, you can see this in action. 

            for kid in students["new"]:
       		i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        	i.add_user()
                i.move_user()
		
So, for each kid in students, i = student(). student() is the class. i stands for instance (you can use any variable here, doesn't have to be i, it's just generally used in python as a matter of style), so for each kid create a new instance of the student class, with the attributes defined in parentheses. Remember, each "kid" will be a list, so you can see for the attributes we take a item at a certain list index. The list contains things like name, email, student id, and so on and the class obviously needs this information, so this part is just matching the attributes up. 

    def __init__(self, email, lastname, firstname, password,
                 s_id, grade, department, master_file):
        self.email = email
        self.lastname = lastname
        self.firstname = firstname
        self.password = password
        self.s_id = s_id
        self.grade = grade
        self.department = department
        self.master_file = master_file
	
If you look at the first part of the class we have the __init__ function. This is where we define all the attributes. Self is a commonly used variable in python classes, explained here: https://pythontips.com/2013/08/07/the-self-variable-in-python-explained/

For our purposes, our stuff begins after the self variable. These are sort of like arguments to any other funtion, and get defined in the same order on instantiation. So going back to our import_students() function, when you see the line 
   
    i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
    
You know that kid[2] is email, kid[1] is lastname, kid[0] is firstname, and so on. If you open up the GoogleLogins csv we get from nefec, you can understand this a little bit more clearly. As described before, the list maker function turns this csv into a list of lists, where each list is one line of the csv. So thinking about it like that, as each line being a list, a comma delimits each index of the list. So, for example, a list may look like

list_example = ['JOHN', 'DOE', '12doe.john@union.k12.fl.us', '63Uc123J455']

If I told python, print list_example[0] it will print JOHN

So when instantiating each student object, I am simply telling it which list index corresponds to which variable in the init function. This stuff is kind of hard to grasp, bear with me :) 

If we look at the import_students() function again,

            for kid in students["new"]:
       		i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        	i.add_user()
                i.move_user()
You see after the i = student() part, there is the i.add_user() and i.move_user() This is what calls those methods. Method is a name for a function that is in a class. So the add_user() function that I defined within the class is going to run on this particular instance. 

Section 3.2: The Student Class

    class student(object):

    def __init__(self, email, lastname, firstname, password,
                 s_id, grade, department, master_file):
        self.email = email
        self.lastname = lastname
        self.firstname = firstname
        self.password = password
        self.s_id = s_id
        self.grade = grade
        self.department = department
        self.master_file = master_file

    def add_user(self):
        #this is all the fields gam wants to create a new user
        gam_switch = " ".join([self.email, "firstname", self.firstname, 
                               "lastname", self.lastname, "password",
                               self.password, "UCSDstudent.id", self.s_id,
                               "organization department", self.department,
                               "description", self.grade, "primary"])
        with open(self.master_file, 'a') as f:
            f.write("gam create user {0}\n".format(gam_switch))
    
    #uses department field, which is school number
    def move_user(self):
        school = ""
        if self.department == "0031":
            school = "LBES Students"
        if self.department == "0022":
            school = "LBMS Students"
        if self.department == "0021":
            school = "UCHS Students"
        group = school.replace(" ", "") + "@union.k12.fl.us"
        #tells gam to move user to correct OU
        gam_input = ('gam update org "/Chromebooks'
                     '/Student/{0}" add users {1}\n'
                     .format(school, self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
        #ctells gam to add user to correct group
        gam_input1 = ("gam update group {0} "
                      "add member user {1}\n"
                      .format(group, self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input1)

    def unsuspend(self):
        gam_input = ("gam update user {0} suspended off\n"
                     .format(self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
            
    def change_password(self):
        pass_file = r'C:\users\backend\desktop\google_import\passwords.txt'
        gam_input = ("gam update user {0} password {1}\n"
                     .format(self.email, self.password))
        with open(pass_file, 'a') as f:
            f.write(gam_input)

So this is a big chunk of code. Apart from the actually concept of the class, it's actually really simple stuff here. The first line defines the class, like a function, and then you have the init function. Like discussed in section 3.1, this just defines all the variables that come with the class. You can see blow each one is assined to the self. version of itself. This is a way to make each variable specific to each instance of the class. You will see later on as we go through the class methods they refer to these self. variables, and that just means use the version of that variable specific to this instance. After the init function are the various methods, which look just like regular functions, like the ones discussed in section 2. I will now go over each of those and there purposes.

Section 3.3: The add_user method

    def add_user(self):
        #this is all the fields gam wants to create a new user
        gam_switch = " ".join([self.email, "firstname", self.firstname, 
                               "lastname", self.lastname, "password",
                               self.password, "UCSDstudent.id", self.s_id,
                               "organization department", self.department,
                               "description", self.grade, "primary"])
        with open(self.master_file, 'a') as f:
            f.write("gam create user {0}\n".format(gam_switch))
	    
This one is much simpler than it looks. When you create a user in GAM, you have to fill out every field of information a user has in google. So I create a variable called gam_switch, and use the .join() function to put a list of strings together into one very long string which will be our GAM command. So the final GAM command will look like this:

    gam create user 12doe.john@union.k12.fl.us firstname John lastname Doe password Uc123F45 UCSDstudent.id 12345 organization department /chromebooks/lbesstudents description 02 primary
    
 You can see it just fills in the blanks with the self. variables. Then it opens the master file, and writes that super long create user command to it. Also take note, that the only arguement this and the other methods take is self. This means that it will get the self. version of every variable defined in the init function. Pretty neat.
 
 Section 3.4: The move_user method
 
 
    def move_user(self):
        school = ""
        if self.department == "0031":
            school = "LBES Students"
        if self.department == "0022":
            school = "LBMS Students"
        if self.department == "0021":
            school = "UCHS Students"
        group = school.replace(" ", "") + "@union.k12.fl.us"
        #tells gam to move user to correct OU
        gam_input = ('gam update org "/Chromebooks'
                     '/Student/{0}" add users {1}\n'
                     .format(school, self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
        #ctells gam to add user to correct group
        gam_input1 = ("gam update group {0} "
                      "add member user {1}\n"
                      .format(group, self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input1)

This one is more involved, but still simple. It looks at the self.department variable to determine what school this student is at. You can see some if statements here, which simply match the school number to the actual school. Then you have the variable group, which takes the newly assigned school variable and does some light formatting, namely taking the space out and adding @union.k12.fl.us to the end. So group will be a google group, or email address. Then like some other methods and functions, opens the master file and writes the gam command to move the user to the correct OU and add them to the correct group. Note here, that there is no lbesstudents group, because the students at LBES do not have gmail. The script will attempt to add them to lbesstudents@union.k12.fl.us group, but will fail when GAM issues the command. This can be safely ignored. It would require more complex code to add an if else statement to ignore the LBES students, and I deemed not really worth the added complexity since it fails harmlessly.

Section 3.5: the unsuspend method

    def unsuspend(self):
        gam_input = ("gam update user {0} suspended off\n"
                     .format(self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
	    
This is another super easy one. It just adds the command to unsuspend a user to the master file, using the same code as pretty much every other function that accesses the master file. 

Section 3.6: The change_password method.

    def change_password(self):
        pass_file = r'C:\users\backend\desktop\google_import\passwords.txt'
        gam_input = ("gam update user {0} password {1}\n"
                     .format(self.email, self.password))
        with open(pass_file, 'a') as f:
            f.write(gam_input)
	    
So, here we change everyone's passwords to what is listed in the nefec csv. We need to know kids passwords, which are listed in skyward, and if they change it then the script simply changes it back. It does this on every single student. First thing I do is define where the password file is. I chose to do this within the method, since this is the only time it will be accessed. And later when we actually call the update_passwords function, I define it there manually too. Otherwise I would have to add it ass an attribute to the class, and it is really just unneccessary. Also of note, notice when we open it, we open it as 'a', which means append. We are writing our update password commands to the end of the file.


********************************************************************************************************************************
     
PART 4
THE GAM MASTER FUNCTION

Section 4.1: The master philosophy

So this last function, is a very important one. It is similar to the main() function, in that this is where all the action takes place, and it does several things. I debated including all of this in the main function, but decided not to, in hopes to make the script a little easier to understand. I wrote this function after a major update to this script. Before, all the times you see in the script where it opens the master file and issues commands, it used to call gam on the spot. When I reworked it, I changed all those commands to instead write those commands to the master file. At this point it was necessary to actually create a function to run said master file. This is it. Let's dive in.

Section 4.2: The master function itself

    def gam_master(master_file):
        pass_file = r'C:\users\backend\desktop\google_import\passwords.txt'
        #make sure gam runs these commands one at a time, in order
        try:
            subprocess.call('set GAM_THREADS=1', shell=True)
            logging.info("Set gam to single threaded mode.")
        except:
            logging.warning("Could not set gam to single thread"
                            "Aborting to prevent errors...")
            exit()
        #call gam to run a batch operation on master_file and capture stdout
        p1 = subprocess.Popen(['gam', 'batch', master_file], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        out1, err1 = p1.communicate()
        logging.info(out1)
        logging.warning(err1)
        #set gam to run 20 update password commands at once
        try:
            subprocess.call('set GAM_THREADS=20', shell=True)
            logging.info("Set gam to multi threaded mode.")
        except:
            logging.warning("Could not set GAM to multi-threaded mode...proceeding")
        p2 = subprocess.Popen(['gam', 'batch', pass_file], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        out2, err2 = p2.communicate()
        logging.info(out2)
        logging.warning(err2)

        """There's no real need to make a new password file everytime this runs,
        or really keep a record of the commands it ran to update passwords.
        These two lines simply delete the contents of pass_file so every command 
        the file starts fresh everytime it runs.
        """ 
   
        cleanup = open(pass_file, 'w')
        cleanup.close
	
This is the function in its glorious entirety. First thing it does, is define where the password file is. It will get the location of the master file through an argument. Remember we defined the password file inside a class method, so python will have forgot about it by the time this funtion runs, and we aren't passing it on as an argument, so we need to define it here. We could define it as an argument, but it would take the same amount of code and incur no real benefits, either in efficiency or clarity. 

What's gonna happen next is we are going to use some try: except: statements. These allow us to handle errors. First statement will use subprocess.call() to send a command to windows, that command being 'set GAM_THREADS 1' which will tell GAM to run one command at a time, in the order that it reads them. This is important for one major reason. When GAM runs multi threaded, it runs commands in no particular order, and several at a time. If in my master file, I have a command to create a user, and another to move the newly created user, we run into issues where it may run the move user command before the create user command. There will obviously be no user there to move, it will throw an error and move on to create the user, but leave the user without moving it since that command already failed. This is a problem.

If when it runs this call() function, (remember it is in the try: block) there is an error, it moves to execute the code in the except: block. You can see there are logging commands in both blocks to let us know if it was successful or not. There is the exit() function in the except block, which will close the whole script. If GAM can't be set to single thread here, we don't want to even run it, as it will make a mess. 

Also of note, students don't usually come and go in large numbers, so running this part in single thread doesn't slow the execution down very much, since there will likely only be a handfull of commands to run.


    p1 = subprocess.Popen(['gam', 'batch', master_file], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        out1, err1 = p1.communicate()
        logging.info(out1)
        logging.warning(err1)

Ok so here is where it gets to work. We are going to use subprocess.Popen() to call GAM, for the extra granularity it provides. Popen takes a list as the first argument, and the items in the list are the commands and arguments it's gonna send to the OS. In our case 'gam', 'batch' and the master_file variable. Windows will see 'gam batch C:\users\backend\desktop\google_import\master\masterfile.txt' as a result of this. The other two arguments are sending the stdout and stderr to pipe to python's subprocess module. This means that the output and error codes that windows sees while running this command will pipe back to python. I then assign out1, and err1 to the pip of p1 (which is the variable name for the Popen process we just ran), and use the communicate method to capture it. I then write it to the logfile with the stdout as info, and stderr as warnings. In this way, we capture everything that goes on in the windows command window to the log file. So we get all of GAM's output and errors, and can see verbose information of every little thing that goes on. 

Section 4.3: Passwords

The second part of this function deals with passwords. We are going to see an nearly identical try except statement, where we try to set gam to run at 20 threads. This will execute 20 commands at once, which is about the max that google's API will allow before wigging out. Notice here we are not going to exit even if it fails, we are just going to log that it failed. It won't hurt anything here, it will just take a lot longer to update everyone's passwords.

    p2 = subprocess.Popen(['gam', 'batch', pass_file], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        out2, err2 = p2.communicate()
        logging.info(out2)
        logging.warning(err2)

This next part is pretty much the same as before. We are going to run a batch operation with GAM, except the commands are in pass_file, which has a bunch of update user password commands, for every student in the district. We are going to again capture stdout and stderr and write it to the log.

    cleanup = open(pass_file, 'w')
    cleanup.close
    
The last two lines simply open the passfile and erase everything. Remember we add to the passfile using append? It's important to clean it up after we are done with it, and we can start fresh again every time the script is run. It is simpler and quicker than iterating through the file and looking for changes, and updating it as needed. It is better to just blow it out and start from scratch. We don't need verbose logging here, as we will have stdout of the result of these commands in the actual log, and all the commands will always be gam update user [email] password [password]. 



********************************************************************************************************************************

PART 5
Service

Due to constant issues with Task Scheduler, I decided to instead run a very lightweight service that would kick off the import on a schedule. This is the import_service file. It has one main dependency, and that is a python class called SMWinservice. It is a class that you can inherit to build your own windows services. It is just a py file that you drop in your pythonroot\lib folder. Instructions can be found here: https://www.thepythoncorner.com/2018/08/how-to-create-a-windows-service-in-python/?doing_wp_cron=1551278840.5138919353485107421875

The service itself is really simple. It runs constantly and looks at the hour. If it is not 11pm, it waits 45 minutes and checks again and repeats until the hour is 23 (11 pm). If it is, it kicks off the main google import program, and sleeps for an hour before the process begins again.

At the top of this file you have your familiar imports, then you move on to the service object, which we inherit from SMWinservice. Then we define a couple attributes, includeing the service name, the display name, and description. These three attribute show up when looking at the service in windows. Then there are two methods (functions) where we tell the service what to do when it is started and stopped. For both methods we simply change the isRunning attribute to true or false respectively. EZ pz. Lastly we have the main method. Here is where the actual logic goes. First thing it does is sets up a while loop. The condition of this loop is that the attribute isRunning has to be equal to true. So while the script hasn't been stopped, do the following:

Next it gets the current time and stores it in the time variable defined on line 21. Note here that when using the time.strftime() function, you can format the output via a string arguement, which is the in the parentheses, in this case '%H'. This tells the function to just get the hour, because that is all we really need here.

Then we have a simple if else control. If the hour is 23, then call the main google_importer program. Then sleep for an hour while it runs, then check the time again. This will then cause it to reevaluate the logic again, so long as isRunnning still equals true.

Since it has been an hour at this point, time will no longer equal 23, which means it will instead hit the else logic. The else statement is very simple as well. Wait 45 minutes and then it sets the time variable again at which point the process repeats. It does this until the service is stopped or it is 11pm again, at which point it will call google_import again. 

To maintain the service, simply open services.msc and look for the Google Student Importer service. This all runs on the Utilities server, by the way. Start the service like you normally would any other service, and stop it the same way if you ever need to.


********************************************************************************************************************************
     
PART 6
IN CLOSING

Section 6.1: Closing remarks

That's it. That's the whole script. Hopefully I have made it somewhat less arcane, and more accessible. I would not want anyone to ever be faced with this script and decide it is easier to learn to code and write another, instead of master what has already been done. The script is super fast and efficient. GAM takes a while to run it's commands, but the actual python part of this script executes in less than a second. I feel it is very readable, and it's logic somewhat easy to follow, and this long ass readme can clear up anything not self explanatory. 

Section 6.2: The Future

In the future I want to make a few updates to this script, mostly in the form of new features. I would like to add some sysargs, which would allow us to run this exe with switches to modify it's behavior. Such as, I would like to add the functionality to go through every student and call the move_user method, and also a graduate function to move all graduating 4th graders to 5th grade, and all graduating 8th graders to 9th grade. We have to do this every year, it would make sense to add it to this program. As it is, this program is completely debugged and works flawlessly. It has ran everyday for many months with a total of zero errors. As far as improving it, it's pretty much there. It runs as fast as GAM can go since I added multithreading, the logging is as good as it can be or needs to be. It could probably be generalized to use an ini file the defines alot of the variables, so it can be used in other districts. Active Directory integration is also a feature I have considered. 
