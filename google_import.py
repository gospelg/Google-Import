import csv
from subprocess import call
import time
import logging

date = time.strftime("%d_%m_%Y")
logging.basicConfig(filename='C:\users\backend\desktop\google_import\logs\log{0}.log'.format(date), level=logging.DEBUG)

#create a student object. All students have these several attributes, gleaned from the nefec csv
class student(object):
			
	def __init__(self, email, lastname, firstname, password, s_id, grade, department):
		self.email = email
		self.lastname = lastname
		self.firstname = firstname
		self.password = password
		self.s_id = s_id
		self.grade = grade
		self.department = department
	
	def add_user(self):
		#this is all the fields gam wants to create a new user
		gam_switch = " ".join([self.email, self.firstname, self.lastname, self.password, self.s_id, self.grade])
		#creates the user in google
		try:
			call("C:\Users\backend\Desktop\gam-64\gam.exe create user {0}".format(gam_switch))
			logging.info("Created user {0} \n".format(gam_switch[0]))
		except:
			logging.warning("Failed to create user {0} \n".format(gam_switch[0]))

	def move_user(self):
		school = ""
		if self.department == "0031":
			school = "LBES Students"
		if self.department == "0022":
			school = "LBMS Students"
		if self.department == "0021":
			school = "UCHS Students"
		group = school.replace(" ", "") + "@union.k12.fl.us"
		try:
			#calls gam to move user to correct OU
			call('C:\Users\backend\Desktop\gam-64\gam.exe update org "/Chromebooks/Student/{0}" add users {1}'.format(school, self.email))
			#calls gam to add user to correct group
			call("C:\Users\backend\Desktop\gam-64\gam.exe update group {0} add member user {1}".format(group, self.email))
			logging.info("Sucessfully moved user {0} to new group and OU \n".format(self.email))
		except:
			logging.warning("Could not move user {0} to new group or OU \n".format(self.email))

#unsuspends account			
	def unsuspend(self):
		try:
			Call("C:\Users\backend\Desktop\gam-64\gam.exe update user {0} suspended off".format(self.email))
			logging.info("Reactivated account for {0} \n".format(self.email))
		except:
			logging.warning("Could not reactivate account for {0}".format(self.email))
	
#for item in nefec, item[11] is the student id. for x in google, x[3] is also student id, and x[1] is suspended, true or false.
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

#student[3] is student id field. If there is nothing in this field, the function leaves it alone. In this way it will never affect staff
#student[1] is whether the student account is suspended or not. Item[11] is student id in the nefec csv
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

#arguement is a dictionary, as exported from new students function. This allows easy seperation of which students are new and which just need to have accounts unsuspended
def import_students(students):
	for kid in students["new"]:
		i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
		i.add_user()
		i.move_user()
	for kid in students["unsuspend"]:
		i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
		i.unsuspend()
		i.move_user()
		
def remove_students(students):
	for kid in students:
		try:
			#suspends user. Did not do this through class, becasue the only attribute needed is email. Students will be a straightforward list of emails of kids to suspend. 
			call("C:\Users\backend\Desktop\gam-64\gam.exe update user {0} suspended on".format(kid))
			#moves them to suspended users ou
			call('C:\Users\backend\Desktop\gam-64\gam.exe update org "/Suspended Users" add users {0}'.format(kid)
			logging.info("Sucessfully suspended user {0} and moved to suspended OU \n".format(kid))
		except:
			logging.warning("Could not suspend {0} or move to suspended OU \n".format(kid))
		
#converts csv files to tuples  so they dont have to be reopened every time they need to be accessed. 	
def list_maker(file_path):
	with open(file_path, 'r') as f:
		reader = csv.reader(f, delimiter=',')
		next(reader, None)
		new_list = list(reader)
		return new_list
		
#combines homeschool logins with regular logins and turns them into one tuple 
def combiner(list1, list2):
	for item in list2:
		list1.append(item)
	return tuple(list1)
			
def main (): 
	
	#makes gam print out a csv of all the users in GAD, with all fields to a csv
	call("C:\Users\backend\Desktop\gam-64\gam.exe print users suspended custom UCSDstudent > C:\users\backend\desktop\google_import\student_id.csv")
	sleep(15)

	#assign files to variables
	logins = list_maker("C:\users\backend\desktop\google_import\sftp\GoogleLogins.csv")
	home_logins = list_maker("C:\users\backend\desktop\google_import\sftp\GoogleLoginsHomeSchool.csv")
	gam_output = list_maker("C:\users\backend\desktop\google_import\student_id.csv")
	
	logins = combiner(logins, home_logins)
	
	users_add = new_students(logins, gam_output)
	users_remove = gone_students(logins, gam_output)
	
	import_students(users_add)
	remove_students(users_remove)
	
main()
