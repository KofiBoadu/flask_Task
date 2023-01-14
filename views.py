import sqlite3
from functools import wraps
from flask import Flask,flash, redirect, render_template, request, session , url_for,g
from forms import AddTaskForm


app=Flask(__name__)
app.config.from_object('_config')


def connect_db():
	"""
	connect_db() - Connects to the database specified in the app's config file.

	Returns:
	A connection object to the specified database.
	"""
	return sqlite3.connect(app.config["DATABASE"])


def login_required(test):
	"""
	login_required(test) - A decorator function that checks if the user is logged in before allowing access to a specific view function.

	The decorator checks for the existence of the 'logged_in' key in the session object.
	 If it exists, the decorated view function is called. Otherwise, the user is redirected to the login page with a message to login first.

	Parameters:
	test (function): The view function that needs to be protected by the decorator.

	Returns:
	A wrapped version of the input function that checks for a valid login before allowing access.

	"""
	@wraps(test)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return test(*args, **kwargs)
		else:
			flash('you need to login first')
			return redirect(url_for('login'))
	return wrap



#route handling
@app.route('/logout/')
def logout():
	"""
	logout() - Logs out the user by removing the 'logged_in' key from the session object, displaying a message and redirecting to the login page.

	This function removes the 'logged_in' key from the session object, effectively logging out the user. 
	It also displays a message "Goodbye" and redirects the user to the login page.

	Returns:
	A redirect response to the login page.

	"""
	session.pop('logged_in',None)
	flash('Goodbye')
	return redirect(url_for('login'))



#login route 
@app.route('/',methods=['GET','POST'])
def login():
	"""
	login() - Handles user login by verifying the provided credentials against the ones specified in the app's config file.

	This function handles the login process for the user by checking the request method. If the request method is 'POST',
	 the function retrieves the provided username and password from the form, verifies them against the USERNAME and PASSWORD specified in the app's config file. 
	 If the credentials are valid, a session variable 'logged_in' is set to True, a message "welcome" is displayed and the user is redirected to the tasks page. 
	 If the credentials are invalid, an error message "Invalid Credentials.Please try again" is displayed and the user is prompted to try again.
	  If the request method is not 'POST', the login template is rendered.

	Returns:
	If the request method is 'POST' and the credentials are valid, redirects the user to the tasks page.
	If the request method is 'POST' and the credentials are invalid, render the login page with an error message.
	If the request method is not 'POST', render the login page.

	"""
	if request.method=='POST':
		if request.form['username'] != app.config['USERNAME'] or request.form['password'] != app.config['PASSWORD']:
			error='Invalid Credentials.Please try again'
			return render_template('login.html',error=error)
		else:
			session['logged_in']= True
			flash('welcome')
			return redirect(url_for('tasks'))
	return render_template('login.html')







@app.route('/tasks')
@login_required
def tasks():
	"""
	tasks() - Retrieves the open and closed tasks from the database and renders the tasks template.

	This function connects to the database, retrieves all open and closed tasks, and stores them in two lists: open_tasks and closed_tasks.
	The open tasks are defined as tasks that have a status of 1 and the closed tasks are defined as tasks that have a status of 0. 
	The function then closes the database connection and renders the tasks template, passing the open and closed tasks lists as well as the AddTaskForm object to the template.

	Returns:
	A rendered template of the tasks page with open and closed tasks lists, and AddTaskForm object.

	"""
	g.db= connect_db()
	cursor= g.db.execute("SELECT name,due_date, priority, task_id FROM tasks WHERE status=1")
	open_tasks=[dict(name=row[0], due_date= row[1],priority=row[2],task_id=row[3]) for row in cursor.fetchall()]
	cursor=g.db.execute("SELECT name, due_date, priority, task_id FROM tasks WHERE status=0")
	closed_tasks=[ dict(name=row[0],due_date=row[1],priority=row[2],task_id=row[3]) for row in cursor.fetchall()]
	g.db.close()
	return render_template('tasks.html',form=AddTaskForm(request.form),open_tasks=open_tasks,closed_tasks=closed_tasks)




@app.route('/add/', methods=['POST'])
@login_required
def new_task():
	"""
	new_task() - Handles the creation of a new task by adding it to the database.

	This function connects to the database, retrieves the name, due date and priority from the form, and checks if all fields are filled.
	 If any field is empty, a message "All fields are required .Please try again" is displayed and the user is redirected to the tasks page. 
	 If all fields are filled, the function adds the new task to the database by executing an insert statement and passing the form's data as the values for the task's name, due date, priority and status (1 for open task). 
	 The changes are then committed to the database and the connection is closed.
	  A message "New entry was successfully posted thanks" is displayed and the user is redirected to the tasks page.

	Returns:
	If any fields is empty, a redirect to the tasks page with an error message.
	If all fields are filled, a redirect to the tasks page with a success message.

	"""
	g.db= connect_db()
	name= request.form['name']
	date= request.form['due_date']
	priority=request.form['priority']
	if not name or not date or not priority:
		flash("All fields are required .Please try again")
		return redirect(url_for('tasks'))
	else:
		g.db.execute("INSERT INTO tasks (name, due_date, priority, status) VALUES(?,?,?,1)",[
			request.form['name'],
			request.form['due_date'],
			request.form['priority']
			])
		g.db.commit()
		g.db.close()
		flash("New entry was successfully posted thanks")
		return redirect(url_for('tasks'))





@app.route('/complete/<int:task_id>/')
@login_required
def complete(task_id):
	"""
	complete(task_id) - Marks a specific task as complete by updating its status in the database.

	This function connects to the database, and updates the status of the task with the specified task_id to 0 (complete) by executing an update statement.
	The changes are then committed to the database and the connection is closed. A message 
	"The task was marked as complete" is displayed and the user is redirected to the tasks page.

	This function is decorated with the login_required decorator, which checks if the user is logged in before allowing access to the function.

	Parameters:
	task_id (int): The ID of the task that needs to be marked as complete.

	Returns:
	A redirect to the tasks page with a success message.

	"""
	g.db= connect_db()
	g.db.execute("UPDATE tasks SET status= 0 WHERE task_id="+str(task_id))
	g.db.commit()
	g.db.close()
	flash("The task was marked as complete")
	return redirect(url_for('tasks'))





@app.route('/delete/<int:task_id>/')
@login_required
def delete_entry(task_id):
	"""
	delete_entry(task_id) - Deletes a specific task from the database.

	This function connects to the database, and deletes the task with the specified task_id by executing a delete statement.
	 The changes are then committed to the database and the connection is closed. A message 
	 "The task was deleted" is displayed and the user is redirected to the tasks page.

	Parameters:
	task_id (int): The ID of the task that needs to be deleted.

	Returns:
	A redirect to the tasks page with a success message.

	"""
	g.db=connect_db()
	g.db.execute("DELETE FROM tasks WHERE task_id="+str(task_id))
	g.db.commit()
	g.db.close()
	flash("The task was deleted")
	return redirect(url_for('tasks'))



