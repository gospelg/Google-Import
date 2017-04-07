#####################################################################################
#                         Garrett's super duper google importer                     #
#                                     version 2.3.2                                 #
#         Read me located on DC2 "C:\users\backend\google_import\readme.txt         #
#####################################################################################

from subprocess import call
import csv
import time
import logging

#create a student object. All students have these several attributes, gleaned from the nefec csv
class student(object):

    gam = r"C:\Users\backend\Desktop\gam-64\gam.exe"

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
        gam_switch = " ".join([self.email, self.firstname, self.lastname,
                               self.password, self.s_id, self.grade])
        try:
            call("{0} create user {1}".format(self.gam gam_switch), shell=True)
            logging.info("Created user {0}"
                         .format(self.email))
        except:
            logging.warning("Failed to create user {0}"
                            .format(self.email))

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
            gam_input = ('{0} update org "/Chromebooks'
                         '/Student/{1}" add users {2}'
                         .format(self.gam school, self.email))
            call(gam_input, shell=True)
            #calls gam to add user to correct group
            gam_input1 = ("{0} update group {1} "
                          "add member user {2}"
                          .format(self.gam group, self.email))
            call(gam_input1, shell=True)
            logging.info("Sucessfully moved user {0} to new group and OU"
                         .format(self.email))
        except:
            logging.warning("Could not move user {0} to new group or OU"
                            .format(self.email))

    def unsuspend(self):
        try:
            gam_input = ("{0} update user {1} suspended off"
                         .format(self.gam self.email))
            call(gam_input, shell=True)
            logging.info("Reactivated account for {0}"
                         .format(self.email))
        except:
            logging.warning("Could not reactivate account for {0}"
                            .format(self.email))

    def change_password(self):
        try:
            gam_input = ("{0} update user {1} password {2}"
                         .format(self.gam self.email, self.password))
            call(gam_input, shell=True)
            logging.info("Successfully updated password for {0}"
                         .format(self.email))
        except:
            logging.warning("Could not update password for {0}"
                            .format(self.email))

def update_passwords(students):
    for kid in students:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
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
def import_students(students):
    for kid in students["new"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        i.add_user()
        i.move_user()
    for kid in students["unsuspend"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], kid[5], kid[4])
        i.unsuspend()
        i.move_user()

#suspends user. Did not do this through class, becasue the only attribute needed is email.
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

main()
