import csv
from subprocess import call
from time import sleep

class student(object):
			
	def __init__(self, email, lastname, firstname, password, id, ou, grade, department):
		self.email = email
		self.lastname = lastname
		self.firstname = firstname
		self.password = password
		self.id = id
		self.ou = ou
		self.grade = grade
		self.department = department
	
	student_data = [self.email, self.firstname, self.lastname, self.password, self.id, self.ou, self.grade]
	
	def add_user(self):
		gam_switch = " ".join(student_data)
		#creates the user in google
		call("C:\Users\crosbyg\Desktop\gam-64\gam.exe create user {0}".format(gam_switch))
		
	def remove_user(self):
		#suspends user
		call("C:\Users\crosbyg\Desktop\gam-64\gam.exe update user {0} suspended on".format(self.email))
		#moves them to suspended users ou
		call('C:\Users\crosbyg\Desktop\gam-64\gam.exe update org "/Suspended Users" add users {0}'.format(self.email))
	
	def move_user(self):
		school = ""
		if self.department == "31":
			school = "LBES Students"
		if self.department == "22":
			school = "LBMS Students"
		if self.department = "21":
			school = "UCHS Students"
		group = school.replace(" ", "") + "@union.k12.fl.us"
		#calls gam to move user to correct OU
		call('C:\Users\crosbyg\Desktop\gam-64\gam.exe update org "/Chromebooks/Student/{0}" add users {1}'.format(school, self.email))
		#calls gam to add user to correct group
		call("C:\Users\crosbyg\Desktop\gam-64\gam.exe update group {0} add member user {1}".format(group, self.email))

#converts csv files to lists for so they dont have to be reopened every time they need to be accessed. 	
def tuple_maker(file_path):
	with open(file_path, 'r') as f:
		reader = csv.reader(f, delimiter=',')
		new_tuple = tuple(reader)
		return new_tuple 

def new_students(nefec, google):
	users_add = {"new":[], "unsuspend": []}
#for item in nefec, item[11] is the student id. for x in google, x[3] is also student id, and x[1] is suspended, true or false.
	for item in nefec:	
		for x in google:
			if item[11] == x[3] and x[1] == "FALSE":
				break
			if item[11] == x[3] and x[1] == "TRUE":
				users_add["unsuspend"].append(item)
				break
		else:
			users_add["new"].append(item)
	return users_add
	

def gone_students(nefec, google):
	deactivate = []
	for student in google:
		if student[3] != "" and student[1] != "TRUE":
			for item in nefec:
				if student[3] in item[11]: 
					break
			else:
				deactivate.append(student[0])
		else:
			pass
				
	return deactivate
	
def main (): 
	#makes gam print out a csv of all the users in GAD, with all fields to a csv
	call("C:\Users\backend\Desktop\gam-64\gam.exe print users suspended custom UCSDstudent > C:\users\backend\desktop\google_import\student_id.csv")
	sleep(20)

	#assign files to variables
	logins = list_maker("C:\users\backend\desktop\google_import\sftp\GoogleLogins.csv")
	home_logins = list_maker("C:\users\backend\desktop\google_import\sftp\GoogleLoginsHomeSchool.csv")
	gam_output = list_maker("C:\users\backend\desktop\google_import\student_id.csv")
	
	users_add = new_students(logins, gam_output)
	users_remove = gone_students(logins, gam_output)
	
	
	
	
	
#needs to update grad year and password, especially password. Needs to check for suspended accounts and bring them back on. Also needs to move groups when changing schools
