#!/usr/bin/python
# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.

### Geo Van O, v0.9, Sep 2013

import subprocess
from time import strptime
import sys
try:
	import git
except ImportError:
	print "This update script requires python-git, please install it with 'sudo apt-get install python-git"
	sys.exit(1)


### call installDependencies.sh, so commands are only defined in one place.
def installDependencies(scriptDir):
	try:
		print "Installing dependencies and fixing permissions..."
		subprocess.check_call(["sudo", "bash", scriptDir + "/installDependencies.sh"], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print "I tried to execute the installDependencies.sh bash script, an error occurred. " + \
		      "Try running it from the command line in your brewpi-script dir"


### Function used if requested branch has not been checked out
def checkout_repo(repo, branch):
	print "Attempting to checkout " + branch
	try:
		repo.git.checkout(branch)
	except git.GitCommandError, e:
		print e
		print "Failed. Ack! Quitting"
		sys.exit()
	print "Success!"


### Stash any local repo changes
def stashChanges(repo):
	stashed = False
	print "Attempting to stash any changes..."
	try:
		resp = repo.git.stash()
		print resp
		stashed = True
	except git.GitCommandError, e:
		print e
		print "Unable to stash, don't want to overwrite your stuff, aborting this branch update"
		sys.exit()
	return stashed


### Function used to stash local changes and update a branch passed to it
def update_repo(repo, branch):
	stashed = False
	repo.git.fetch('origin', branch)
	try:
		print repo.git.merge('origin/' + branch)
	except git.GitCommandError, e:
		print e
		if "Your local changes to the following files would be overwritten by merge" in str(e):
			stashed = stashChanges(repo)
		print "Trying to merge again..."
		try:
			print repo.git.merge('origin/' + branch)
		except git.GitCommandError, e:
			print e
			print "Sorry, local changes made are too complex. Aborting this branch update"
			return

	if stashed:
		print "##################################################################"
		print "#Your local changes are in conflict with the last update of code.#"
		print "##################################################################"
		print "The conflict is:\n"
		print "-------------------------------------------------------"
		print  repo.git.stash("show", "--full-diff", "stash@{0}")
		print "-------------------------------------------------------"
		print ""
		print  ("Your changes are stashed for the moment, but if you don't care about them, I can discard them now." +
		       "If I don't, you need to resolve this on your own, or you'll have issues updating BrewPi in the future.")
		choice = raw_input("Would you like me to discard your local changes causing this conflict? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			for filename in repo.git.stash("show", "stash@{0}").split("\n")[:-1]:
				repo.git.checkout("--theirs", filename.split("|")[0].strip())
				repo.git.add(filename.split("|")[0].strip())
				print "Discarded changes, merging again, just to be sure..."
				print repo.git.merge('origin/' + branch)
	print branch + " updated!"


### Function to be used to check most recent commit date on the repo passed to it
def check_repo(repo):
	repoChanged = False
	repo.git.fetch()
	curBranch = ""
	branch = ""
	branches = repo.git.branch('-r').split('\n')
	branches.remove("  origin/HEAD -> origin/master")
	branches = [x.lstrip(" ").strip("* ").replace("origin/", "") for x in branches]
	print "\nAvailable branches in " + str(repo).split("\"")[1] + ":"
	for i in enumerate(branches):
		print "[%d] %s" % i
	print "[" + str(len(branches)) + "] Skip"
	while 1:
		try:
			selection = int(raw_input("Enter the number of the branch you wish to update: "))
		except ValueError:
			print "Use the number!"
			continue
		if selection == len(branches):
			return False
		try:
			branch = branches[selection]
		except IndexError:
			print "Not a valid selection. Try again"
			continue
		break

	### Check if branch is currently active, if not, prompt to check it out
	branches = repo.git.branch()
	for i in branches.split("\n"):
		if "*" in i:
			curBranch = i
			break
	if curBranch.strip("* ") != branch:
		choice = raw_input("You chose " + branch + " but it is not your current active branch- " +
		                   "would you like me to check it out for you now? (Required to continue) [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			try:
				print repo.git.checkout(branch)
				print "Successfully switched to " + branch
				repoChanged = True
			except git.GitCommandError, e:
				if "Your local changes to the following files would be overwritten by checkout" in str(e):
					print "Local changes exist in your current files that need to be stashed"
					stashed = stashChanges(repo)
					print "Trying to checkout again..."
				try:
					print repo.git.checkout(branch)
				except git.GitCommandError, e:
					print e
					print "I was unable to checkout. Please try it manually from the command line and re-run this tool"
					return False
		else:
			print "Skipping this branch"
			return False

	local = repo.git.show(branch).split("\n")[2]
	if "Date" not in local:
		local = repo.git.show(branch).split("\n")[3]
	remote = repo.git.show('origin/' + branch).split("\n")[2]
	if "Date" not in remote:
		remote = repo.git.show('origin/' + branch).split("\n")[3]
	repoName = repo.git.remote('-v').split(":")[1].split()[0]
	localDate = strptime(local[8:-6], "%a %b %d %H:%M:%S %Y")
	remoteDate = strptime(remote[8:-6], "%a %b %d %H:%M:%S %Y")

	print "\nChecking for updates on " + repoName + ", branch " + branch
	print "Your local copy of " + repoName + " is current as of: " + local
	print "The most current version of BrewPi for this branch is " + remote
	if localDate < remoteDate:
		print "*** Your local version of " + repoName + " is out of date."
		choice = raw_input("Would you like to update this branch? [Y/n]: ")
		if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
			update_repo(repo, branch)
			repoChanged = True
	else:
		print "Your local version of " + repoName + " is good to go!"
	return repoChanged

print "####################################################"
print "####                                            ####"
print "####      Welcome to the BrewPi Updater!        ####"
print "####                                            ####"
print "####################################################"
print ""
print "Most users will want to select the 'master' choice at each of the following menus."
branch = raw_input("Press enter to continue: ")

changed = False
scriptPath = '/home/brewpi'
webPath = '/var/www'

for i in range(3):
	try:
		changed = check_repo(git.Repo(scriptPath)) or changed
	except git.NoSuchPathError:
		print "The path %s does not exist" % scriptPath
		choice = raw_input("What path did you install the BrewPi python scripts to? ")
	except git.InvalidGitRepositoryError:
		print "The path %s does not seem to be a valid git repository" % scriptPath
		choice = raw_input("What path did you install the BrewPi python scripts to? ")
	else:
		break
else:
	print "Maximum number of tries reached, updating BrewPi scripts aborted"

for i in range(3):
	try:
		changed = check_repo(git.Repo(webPath)) or changed
	except git.NoSuchPathError:
		print "The path %s does not exist" % scriptPath
		choice = raw_input("What path did you install the BrewPi web interface scripts to? ")
	except git.InvalidGitRepositoryError:
		print "The path %s does not seem to be a valid git repository" % webPath
		choice = raw_input("What path did you install the BrewPi python scripts to? ")
	else:
		break;
else:
	print "Maximum number of tries reached, updating BrewPi web interface aborted"

if changed:
	installDependencies(scriptPath)

print "Done updating BrewPi!"
