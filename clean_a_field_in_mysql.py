import mysql.connector
import datetime

# Autolab database has an issue that causes wasteful space use:
# For each job submission (indexed by submission_id), there may
# be multiple tests/problems, each indexed with problem_id.
# Each entry in the "scores" table represents a submission+problem.
"""
+---------------+------------+------+-----+---------+----------------+
| Field         | Type       | Null | Key | Default | Extra          |
+---------------+------------+------+-----+---------+----------------+
| id            | int(11)    | NO   | PRI | NULL    | auto_increment |
| submission_id | int(11)    | YES  | MUL | NULL    |                |
| score         | float      | YES  |     | NULL    |                |
| feedback      | mediumtext | YES  |     | NULL    |                |
| problem_id    | int(11)    | YES  | MUL | NULL    |                |
| created_at    | datetime   | YES  |     | NULL    |                |
| updated_at    | datetime   | YES  |     | NULL    |                |
| released      | tinyint(1) | YES  |     | 0       |                |
| grader_id     | int(11)    | YES  |     | NULL    |                |
+---------------+------------+------+-----+---------+----------------+
"""
# feedback is largest field, up to multiple MB.  It contains the
# log+scores returned by Tango for the submission.  However the feedback
# is the SAME for all problems in the submission.
# That means the same log is duplicated into the entries for all the
# problems.  In practice, when the user asks to see the log (output)
# from the web UI for the submission, only the feedback for the first
# problem (with the smallest problem_id) is shown.
# Therefore, the feedback field for all problems but the first one
# in the same submission can be purged to save space.
#
# That's the purpose of this script.

mydb = mysql.connector.connect(
    host="localhost",  # or ip of the db or db container
    user="root",
    passwd="",
    database="app_autolab_development"
)
mycursor = mydb.cursor()

# get the first problem entry for each submission
mycursor.execute("select submission_id, min(problem_id) from scores group by submission_id")
keep = mycursor.fetchall()
toKeep = sorted(keep, key=lambda element: (element[0]))
for x in toKeep:
    print "keep", x
print "total items to keep", len(toKeep)

# get all entries and sort on submission/problem
mycursor.execute("select submission_id, problem_id from scores")
allItems = mycursor.fetchall()
sortedItems = sorted(allItems, key=lambda element: (element[0], element[1]))
for x in sortedItems:
    print "all, sorted", x
print "total items", len(sortedItems)

# get items to purge their feedback column
toPurge = []
for keep in toKeep:
    while True:
        found = next((x for x in sortedItems if x[0] == keep[0]), None)
        if not found:
            break
        if found[1] != keep[1]:
            print "purge", found
            toPurge.append(found)
        sortedItems.remove(found)  # remove to speed up the search
print "total items to purge", len(toPurge)

currentTime = str(datetime.datetime.now())        
for x in toPurge:
    updateCmd = "update scores set feedback = 'purged on %s' where submission_id=%s and problem_id=%s" % (currentTime, x[0], x[1])
    try:
        print "update cmd:", updateCmd
        # DANGER: comment out the following line before you have verified the print out!!!
        mycursor.execute(updateCmd)
    except mysql.connector.Error as err:
        print("### error updating: {}".format(err))
mydb.commit()
