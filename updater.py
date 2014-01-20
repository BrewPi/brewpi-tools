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
### Elco Jacobs, sept 2013

import subprocess
from time import localtime, strftime
import sys
import os

try:
    import git
except ImportError:
    print "This update script requires python-git, please install it with 'sudo apt-get install python-git"
    sys.exit(1)


### calls update-this-repo, which returns 0 if the brewpi-tools repo is up-to-date
def checkForUpdates():
    try:
        print "Checking whether the update script is up to date"
        subprocess.check_call(["sudo", "bash", os.path.dirname(os.path.realpath(__file__)) + "/update-this-repo.sh"],
                              stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print "The update script was not up-to-date, but it should have been updated. Please re-run updater.py."
        exit(1)


### call installDependencies.sh, so commands are only defined in one place.
def runAfterUpdate(scriptDir):
    try:
        print "Installing dependencies, updating CRON and fixing file permissions..."
        subprocess.check_call(["sudo", "bash", scriptDir + "/utils/runAfterUpdate.sh"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print "I tried to execute the runAfterUpdate.sh bash script, but an error occurred. " + \
              "Try running it from the command line in your <brewpi-script>/utils dir"


### Function used if requested branch has not been checked out
def checkout_repo(repo, branch):
    print "Attempting to checkout " + branch
    try:
        repo.git.checkout(branch)
    except git.GitCommandError, e:
        print e
        print "Checking out branch '%s' failed! Aborting..." % branch
        return False
    print "Success!"
    return True


### Stash any local repo changes
def stashChanges(repo):
    print "\nYou have local changes in this repository, that are prevent a successful merge."
    print "These changes can be stashed to bring your repository back to its original state so we can merge."
    print "Your changes are not lost, but saved on the stash." +\
          "You can (optionally) get them back later with 'git stash pop'."
    choice = raw_input("Would you like to stash local changes? (Required to continue) [Y/n]: ")
    if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
        print "Attempting to stash any changes...\n"
        try:
            repo.git.config('--get', 'user.name')
        except git.GitCommandError, e:
            print "Warning: No user name set for git, which is necessary to stash."
            userName = raw_input("--> Please enter a global username for git on this system: ")
            repo.git.config('--global', 'user.name', userName)
        try:
            repo.git.config('--get', 'user.email')
        except git.GitCommandError, e:
            print "Warning: No user e-mail address set for git, which is necessary to stash."
            userEmail = raw_input("--> Please enter a global user e-mail address for git on this system: ")
            repo.git.config('--global', 'user.email', userEmail)
        try:
            resp = repo.git.stash()
            print "\n" + resp + "\n"
            print "Stash successful"
            return True
        except git.GitCommandError, e:
            print e
            print "Unable to stash, don't want to overwrite your stuff, aborting this branch update"
            return False
    else:
        print "Changes are not stashed, cannot continue without stashing. Aborting update"
        return False


### Function used to stash local changes and update a branch passed to it
def update_repo(repo, remote, branch):
    stashed = False
    repo.git.fetch(remote, branch)
    try:
        print repo.git.merge(remote + '/' + branch)
    except git.GitCommandError, e:
        print e
        if "Your local changes to the following files would be overwritten by merge" in str(e):
            if not stashChanges(repo):
                return False
        print "Trying to merge again..."
        try:
            print repo.git.merge(remote + '/' + branch)
        except git.GitCommandError, e:
            print e
            print "Sorry, cannot automatically stash/discard local changes. Aborting"
            return False

    if stashed:
        print "##################################################################"
        print "#Your local changes were in conflict with the last update of code.#"
        print "##################################################################"
        print "The conflict is:\n"
        print "-------------------------------------------------------"
        print  repo.git.stash("show", "--full-diff", "stash@{0}")
        print "-------------------------------------------------------"
        print ""
        print  ("To make merging possible, these changes were stashed." +
                "To merge the changes back in, you can use 'git stash pop'."
                "Only do this if you really know what you are doing!" +
                "Your changes might be incompatible with the update or could cause a new merge conflict.")
    print branch + " updated!"
    return True


### Function to be used to check most recent commit date on the repo passed to it
def check_repo(repo):
    updated = False
    localBranch = repo.active_branch.name
    remoteRef = None

    print "You are currently on branch " + localBranch

    ### Get available remotes
    remote = repo.remotes[0]
    if len(repo.remotes) > 1:
        print "Multiple remotes found in " + repo.working_tree_dir
        for i, rem in enumerate(repo.remotes):
            print "[%d] %s" % (i, rem.name)
        print "[" + str(len(repo.remotes)) + "] Skip updating this repository"
        while 1:
            try:
                choice = raw_input("From which remote do you want to update? [%s]:" % remote)
                if choice == "":
                    print "Updating from default remote %s" % remote
                    break
                else:
                    selection = int(choice)
            except ValueError:
                print "Use the number!"
                continue
            try:
                remote = repo.remotes[selection]
            except IndexError:
                print "Not a valid selection. Try again"
                continue
            break

    repo.git.fetch(remote.name, "--prune")

    ### Get available branches on the remote
    try:
        remoteBranches = remote.refs
    except AssertionError as e:
        print "Failed to get references from remote: " + repr(e)
        print "Aborting update of " + repo.working_tree_dir
        return False

    print "\nAvailable branches on the remote '%s' for %s:" % (remote.name, repo.working_tree_dir)

    for i, ref in enumerate(remoteBranches):
        remoteRefName = "%s" % ref
        if "/HEAD" in remoteRefName:
            remoteBranches.pop(i)  # remove HEAD from list

    for i, ref in enumerate(remoteBranches):
        remoteRefName = "%s" % ref
        remoteBranchName = remoteRefName.replace(remote.name + "/", "")
        if remoteBranchName == localBranch:
            remoteRef = ref
        print "[%d] %s" % (i, remoteBranchName)
    print "[" + str(len(remoteBranches)) + "] Skip updating this repository"

    while 1:
        try:
            choice = raw_input("Enter the number of the branch you wish to update [%s]:" % localBranch)
            if choice == "":
                print "Keeping current branch %s" % localBranch
                break
            else:
                selection = int(choice)
        except ValueError:
            print "Use the number!"
            continue
        if selection == len(remoteBranches):
            return False
        try:
            remoteRef = remoteBranches[selection]
        except IndexError:
            print "Not a valid selection. Try again"
            continue
        break

    if remoteRef is None:
        print "Could not find branch selected branch on remote! Aborting"
        return False

    remoteBranch = ("%s" % remoteRef).replace(remote.name + "/", "")

    checkedOutDifferentBranch = False
    if localBranch != remoteBranch:
        choice = raw_input("You chose " + remoteBranch + " but it is not your currently active branch - " +
                           "would you like me to check it out for you now? (Required to continue) [Y/n]: ")
        if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
            try:
                print repo.git.checkout(remoteBranch)
                print "Successfully switched to " + remoteBranch
                checkedOutDifferentBranch = True
            except git.GitCommandError, e:
                if "Your local changes to the following files would be overwritten by checkout" in str(e):
                    print "Local changes exist in your current files that need to be stashed to continue"
                    if not stashChanges(repo):
                        return
                    print "Trying to checkout again..."
                try:
                    print repo.git.checkout(remoteBranch)
                    checkedOutDifferentBranch = True
                    print "Checkout successful"
                except git.GitCommandError, e:
                    print e
                    print "I was unable to checkout. Please try it manually from the command line and re-run this tool"
                    return False
        else:
            print "Skipping this branch"
            return False

    if remoteRef is None:
        print "Error: Could not determine which remote reference to use, aborting"
        return False

    localDate = repo.head.commit.committed_date
    localDateString = strftime("%a, %d %b %Y %H:%M:%S", localtime(localDate))
    localSha = repo.head.commit.hexsha
    localName = repo.working_tree_dir

    remoteDate = remoteRef.commit.committed_date
    remoteDateString = strftime("%a, %d %b %Y %H:%M:%S", localtime(remoteDate))
    remoteSha = remoteRef.commit.hexsha
    remoteName = remoteRef.name
    alignLength = max(len(localName), len(remoteName))

    print "The latest commit in " + localName.ljust(alignLength) + " is " + localSha + " on " + localDateString
    print "The latest commit on " + remoteName.ljust(alignLength) + " is " + remoteSha + " on " + remoteDateString

    if localDate < remoteDate:
        print "*** Updates are available! ****"
        choice = raw_input("Would you like to update " + localName + " from " + remoteName + " [Y/n]: ")
        if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
            updated = update_repo(repo, remote.name, remoteBranch)
    else:
        print "Your local version of " + localName + " is up to date!"
    return updated or checkedOutDifferentBranch


print "####################################################"
print "####                                            ####"
print "####      Welcome to the BrewPi Updater!        ####"
print "####                                            ####"
print "####################################################"
print ""
checkForUpdates()
print ""

print "Most users will want to select the 'master' choice at each of the following menus."
branch = raw_input("Press enter to continue... ")

changed = False
scriptPath = '/home/brewpi'
webPath = '/var/www'

print "\n\n*** Updating BrewPi script repository ***"
for i in range(3):
    correctRepo = False
    try:
        scriptRepo = git.Repo(scriptPath)
        gitConfig = open(scriptPath + '/.git/config', 'r')
        for line in gitConfig:
            if "url =" in line and "brewpi-script" in line:
                correctRepo = True
                break
        gitConfig.close()
    except git.NoSuchPathError:
        print "The path '%s' does not exist" % scriptPath
        scriptPath = raw_input("What path did you install the BrewPi python scripts to?")
        continue
    except (git.InvalidGitRepositoryError, IOError):
        print "The path '%s' does not seem to be a valid git repository" % scriptPath
        scriptPath = raw_input("What path did you install the BrewPi python scripts to?")
        continue

    if not correctRepo:
        print "The path '%s' does not seem to be the BrewPi python script git repository" % scriptPath
        scriptPath = raw_input("What path did you install the BrewPi python scripts to?")
        continue
    changed = check_repo(scriptRepo) or changed
    break
else:
    print "Maximum number of tries reached, updating BrewPi scripts aborted"

print "\n\n*** Updating BrewPi web interface repository ***"
for i in range(3):
    correctRepo = False
    try:
        webRepo = git.Repo(webPath)
        gitConfig = open(webPath + '/.git/config', 'r')
        for line in gitConfig:
            if "url =" in line and "brewpi-www" in line:
                correctRepo = True
                break
        gitConfig.close()
    except git.NoSuchPathError:
        print "The path '%s' does not exist" % webPath
        webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
        continue
    except (git.InvalidGitRepositoryError, IOError):
        print "The path '%s' does not seem to be a valid git repository" % webPath
        webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
        continue
    if not correctRepo:
        print "The path '%s' does not seem to be the BrewPi web interface git repository" % webPath
        webPath = raw_input("What path did you install the BrewPi web interface scripts to? ")
        continue
    changed = check_repo(webRepo) or changed
    break
else:
    print "Maximum number of tries reached, updating BrewPi web interface aborted"

### Check if wifi is present, and if it is not already added to cron.d file
try:
    with open('/etc/cron.d/brewpi') as f:
        contents = f.read()
    if "enableWlan.sh" not in contents:
        wlanCheck = subprocess.Popen(["ifconfig|grep wlan"], shell = True, stdout = subprocess.PIPE)
        if wlanCheck.stdout.read():
            print "\nIt looks like you're running a wifi adapter on your Pi"
            print "We recently added a utility script that can attempt to re-enable the WiFi connection on your Pi"
            choice = raw_input ("if the connection were to drop. Would you like to install it now? [Y/n]: ")
            if (choice is "") or (choice is "Y") or (choice is "y") or (choice is "yes") or (choice is "YES"):
                print "\n"
                wlanInstall = subprocess.Popen(["sudo "+scriptPath+"/utils/wifiChecker.sh install"], shell = True, stdout = subprocess.PIPE)
                print wlanInstall.stdout.read()
except (IOError):
    print "ERROR: Could not find/open /etc/cron.d/brewpi"

if changed:
    print "\nOne our more repositories were updated, running runAfterUpdate.sh from %s/utils..."
    runAfterUpdate(scriptPath)
else:
    print "\nNo changes were made, skipping runAfterUpdate.sh."
    print "If you encounter problems, you can start it manually with:"
    print "sudo %s/utils/runAfterUpdate.sh" % scriptPath

print "\nDon't forget to reprogram your Arduino with the latest hex file " \
      "via the maintenance panel in the web interface."

print "\n\n*** Done updating BrewPi! ***"
