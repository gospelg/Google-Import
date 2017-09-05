#####################################################################################
#                         Garrett's super duper google importer                     #
#                                     version 3.0.3                                 #
#         Read me located on DC2 "C:\users\backend\google_import\readme.txt         #
#####################################################################################

import subprocess
import csv
import time
import logging

""" The class basically has all the attributes of a student, and a few functions.
The functions basically generate commands to pass to GAM. The put them into two txt
files, master file and passwords. The master file has a batch of commands for moving
users and adding and deleting them and stuff like that. The passwords file is a list
of commands to update everyones passwords. After all this the gam_master() function 
calls gam and points to these two files for the list of commands it should execute.
"""


#create a student object. All students have these several attributes, gleaned from the nefec csv
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

def update_passwords(students, master_file):
    for kid in students:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11],
                    kid[5], kid[4], master_file)
        i.change_password()

#item[11] is the student id, x[3] is also student id, and x[1] is suspended, true or false.
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

#student[3] is student id field. Item[11] is student id in the nefec csv
#If there is nothing in this field, the function leaves it alone. #student[1] is suspended or not.
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

#arguement is a dictionary, as exported from new students function.
def import_students(students, master_file):
    for kid in students["new"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], 
                    kid[5], kid[4], master_file)
        i.add_user()
        i.move_user()
    for kid in students["unsuspend"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], 
                    kid[5], kid[4], master_file)
        i.unsuspend()
        i.move_user()

#suspends user. Did not do this through class, becasue the only attribute needed is email.
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

def gam_master(master_file):
    pass_file = r'C:\users\backend\desktop\google_import\passwords.txt'
    #make sure gam runs these commands one at a time, in order
    try:
        subprocess.call('set GAM_THREADS=1', shell=True)
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
    except:
        logging.warning("Could not set GAM to multi-threaded mode...proceeding)
    p2 = subprocess.Popen(['gam', 'batch', pass_file], 
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    out2, err2 = p2.communicate()
    logging.info(out2)
    logging.warning(err2)

def main ():

    root_dir = r'C:\users\backend\desktop\google_import'
    date = time.strftime("%m_%d_%Y")
    logging.basicConfig(filename='{0}\logs\log{1}.log'
                        .format(root_dir, date), level=logging.DEBUG)
    master_file = r"{0}\master\{1}master.txt".format(root_dir, date)

    #makes gam print out a csv of all the users in GAD, with all fields to a csv
    gam_sheet = (r"C:\Users\backend\Desktop\gam-64\gam.exe "
                 r"print users suspended custom UCSDstudent "
                 r"> C:\users\backend\desktop\google_import\student_id.csv")
    subprocess.call(gam_sheet, shell=True)

    #assign files to variables
    logins = list_maker((r"{0}\sftp\GoogleLogins.csv").format(root_dir))
    home_logins = list_maker((r"{0}\sftp\GoogleLoginsHomeSchool.csv").format(root_dir))
    gam_output = tuple(list_maker((r"{0}\student_id.csv").format(root_dir)))

    logins = combiner(logins, home_logins)

    users_add = new_students(logins, gam_output)
    users_remove = gone_students(logins, gam_output)

    import_students(users_add, master_file)
    remove_students(users_remove, master_file)
    update_passwords(logins, master_file)
    
    gam_master(master_file)

main()
