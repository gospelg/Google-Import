#####################################################################################
#                         Garrett's super duper google importer                     #
#                                     version 4.1.3                                 #
#                      Read me located in application's root directory.             #
#####################################################################################

import subprocess
import csv
import time
import logging
import paramiko as pm
import ConfigParser

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
                 s_id, grade, department, master_file, google_email):
        self.email = email
        self.lastname = lastname
        self.firstname = firstname
        self.password = password
        self.s_id = s_id
        self.grade = grade
        self.department = department
        self.master_file = master_file
        self.google_email = google_email
    
    def add_user(self):
            #this is a all the stuff gam needs to make a new user accounts
        gam_switch = " ".join([self.email, "firstname", self.firstname, 
                               "lastname", self.lastname, "password",
                               self.password, "UCSDstudent.id", self.s_id]) 
        with open(self.master_file, 'a') as f:
            f.write("gam create user {0}\n".format(gam_switch))
    
    #uses department field, which is school number
    def move_user(self):
        school = ""
        if self.department == "0031":
            if self.grade == "KG" or "01" or "02":
                school = "LBES Students/LBES Badge Login"
            else:
                school = "LBES Students"
        if self.department == "0022":
            school = "LBMS Students"
        if self.department == "0021":
            school = "UCHS Students"
        #tells gam to move user to correct OU
        gam_input = ('gam update org "/Chromebooks'
                     '/Student/{0}" add users {1}\n'
                     .format(school, self.email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
        #tells gam to add user to correct group
        #there are no groups for elementary school kids, so exclude them
        if self.department != "0031":
            group = school.replace(" ", "") + "@union.k12.fl.us"
            gam_input1 = ("gam update group {0} "
                          "add member user {1}\n"
                          .format(group, self.email))
            with open(self.master_file, 'a') as f:
                f.write(gam_input1)

    def unsuspend(self):
        gam_input = ("gam update user {0} suspended off\n"
                     .format(self.google_email))
        with open(self.master_file, 'a') as f:
            f.write(gam_input)
            
    def update_user(self):
        #gam wants username without the email domain, so we slice off @union.k12.fl.us (16 characters from end, or [:-16]
        username = self.email[:-16]
        gam_switch = " ".join([self.google_email, "firstname", self.firstname, 
                               "lastname", self.lastname, "password",
                               self.password, "UCSDstudent.id", self.s_id,
                               "username", username])
        with open(self.master_file, 'a') as f:
            f.write("gam update user {0}\n".format(gam_switch))
        #if email was updated, google turns the old email into an alias. We want to delete it
        if self.google_email != self.email:
            with open(self.master_file, 'a') as f:
                f.write("gam delete alias {0}\n".format(self.google_email))
        else:
            None

#item[11] is the student id, x[4] is also student id, and x[1] is suspended, true or false 
#when added to the lists, we append x[0] which is the email associated with student id in google
def new_students(nefec, google):
    users_add = {"new":[], "unsuspend": []}
    users_update = []
    #we don't want to update users in this ou
    unmod_ou = "/Chromebooks/Student/UCHS Students/Help Desk"
    for item in nefec:
        for x in google:
            if item[11] == x[4] and x[1] == "False": 
                if x[3] != unmod_ou:
                    item.append(x[0])
                    users_update.append(item)
                    break
                else:
                    break
            if item[11] == x[4] and x[1] == "True":
                item.append(x[0])
                users_add["unsuspend"].append(item)
                break
        else:
            users_add["new"].append(item)
    return users_add, users_update

#student[4] is student id field. Item[11] is student id in the nefec csv
#If there is nothing in this field, the function leaves it alone. #student[1] is suspended or not.
def gone_students(nefec, google):
    deactivate = []
    for student in google:
        if student[4] != "" and student[1] == "False":
            for item in nefec:
                if student[4] in item[11]:
                    break
            else:
                deactivate.append(student[0])
    return deactivate

#arguement is a dictionary, as exported from new students function.
# 0 is a placeholder for google_email, which doesn't exist for new students yet
def import_students(students, master_file):
    for kid in students[0]["new"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], 
                    kid[5], kid[4], master_file, 0)
        i.add_user()
        i.move_user()
    for kid in students[0]["unsuspend"]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], 
                   kid[5], kid[4], master_file, kid[12])
        i.unsuspend()
        i.update_user()
        i.move_user()
    for kid in students[1]:
        i = student(kid[2], kid[1], kid[0], kid[3], kid[11], 
                    kid[5], kid[4], master_file, kid[12])
        i.update_user()
        i.move_user()
#suspends user. Did not do this through class, because the only attribute needed is email.
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
#add double quotes to first name and last name indexes so special characters dont make gam freak
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
    for x in list1:
            x[0] = r'"{0}"'.format(x[0])
            x[1] = r'"{0}"'.format(x[1])
    return tuple(list1)

def gam_master(master_file, pass_file):
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

def sftp_ops(root_dir, date):
    #get sftp connection parameters from config file
    Config = ConfigParser.ConfigParser()
    Config.read('setup.ini')
    host = Config.get('SFTP', 'Server')
    port = 22
    user = Config.get('SFTP', 'Username')
    password = Config.get('SFTP', 'Password')

    connections = (
    ['/Data/googleLogins/GoogleLogins.csv', 
    '{0}\sftp\GoogleLogins.csv'.format(root_dir)],
    ['/Data/googleLogins/GoogleLoginsHomeSchool.csv', 
    '{0}\sftp\GoogleLoginsHomeSchool.csv'.format(root_dir)],
    ['/Data/lanSchool/ClassesByTeacherLoginName.csv', 
    'C:\\lanschool\\ClassesByTeacherLoginName.csv'],
    ['/Data/lanSchool/StudentsForClassByLoginName.csv', 
    'C:\\lanschool\\StudentsForClassByLoginName.csv'],
    )
    
    #set up sftp log
    pm.util.log_to_file("{0}\\sftp\\{1}_sftp_log".format(root_dir, date))
    
    transport = pm.Transport((host, port))
    transport.connect(username=user, password=password)
    sftp = pm.SFTPClient.from_transport(transport)
    
    #it is now connected, begin operations
    #item[0] translates to remote path, item[1] is local path
    for item in connections:
        sftp.get(item[0], item[1])    
    sftp.close()
    
def main ():
    
    date = time.strftime("%m_%d_%Y")
    Config = ConfigParser.ConfigParser()
    Config.read('setup.ini')
    root_dir = Config.get('General', 'AppRootDir')
    master_file = Config.get('General', 'MasterFile') + (
    'master{0}.txt'.format(date))
    password_file = Config.get('General', 'PasswordFile') + (
    'passwordfile.txt')
    
    #ensure gam.exe is in the windows PATH var, if not figure out the path
    if Config.get('General', 'gamisinpath') == 'True':
        gam = 'gam'
    elif Config.has_option('General', 'AltGamPath'):
        gam = Config.get('General', 'AltGamPath')   
    else:
        gam = raw_input('Please specify the path to gam.exe \n')
        Config.set('General', 'AltGamPath', gam)
    
    #set up a log file, with the current date. Debug level catches info, err, and warning.
    logging.basicConfig(filename ='{0}\\logs\\log{1}.log'
                        .format(root_dir, date), level=logging.DEBUG)
    

    #makes gam print out a csv of all the users in GAD, with all fields to a csv
    logging.info("Exporting users from google...")
    gam_sheet = ('{0} print users suspended custom UCSDstudent ou '
                 '> {1}\student_id.csv'.format(gam, root_dir))
    subprocess.call(gam_sheet, shell=True)
    
    #perform SFTP operations
    try:
        sftp_ops(root_dir, date)
    except:
        logging.warning('SFTP OPS failed, check paramiko log.')
        
    #assign files to variables
    logging.info("Making lists...")
    logins = list_maker(('{0}\\sftp\\GoogleLogins.csv').format(root_dir))
    home_logins = list_maker(('{0}\\sftp\\GoogleLoginsHomeSchool.csv').format(root_dir))
    gam_output = tuple(list_maker(('{0}\\student_id.csv').format(root_dir)))

    logins = combiner(logins, home_logins)

    users_add = new_students(logins, gam_output)
    users_remove = gone_students(logins, gam_output)

    import_students(users_add, master_file)
    remove_students(users_remove, master_file)
 
    logging.info("Staring batch operations...")
    
    gam_master(master_file, password_file)

main()
