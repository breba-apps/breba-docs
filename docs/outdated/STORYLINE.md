# Storyline


Simple story line:
You are assisting a user to verify that the documented steps that asked their users to follow actually work.
You will do that by actually running the steps on a clean linux operating system.


1. When program starts, first you need to find the documentation. Ask the user for the location of the documentation. It can be a url, a file or a folder. (Action/Verify)
2. Come up with terminal commands to retrieve that documentation. For example, if the commands are in github, we want to clone the repo. 
   1. If you cannot retrieve the documentation, tell the user why and ask again. (Action Retry)
   3. However, if you can give it another try with different commands, try those commands first, if these fail, then we will ask the user again. (Action Retry)
4. Now we have access the documentation. But we need to find the documentation files. Come up with a command to find documentation files. (right now just .md files) (Action/Verify)
5. Given the list of file paths, we will start reading docs with the top most README.md file.
3. When reading the file, we will identify the goals that can possibly be achieved in this file using terminal commands.
   4. For each goal we will identify the terminal commands in the documentation 
   5. After running the commands provide output for the report
      6. Report contains:
         File
            Goals
               Commands
               Additional data (how to fix/why failed/etc.)






1. User may be a config in case of automatically running job or a CLI user
2. User submits url to the Assistant. 
3. The Assistant will start executing a pipeline of actions (Action grouping TBD)
4. First action is to fetch the REPO. (context is passed from action to action)
   1. Need to define what context is. It could be the text returned from the previous action.
   2. Each action has a verification step, which may define actions depending on result of verification.
   3. Need to define what the verification step is. It could just another action
   4. To verify that the repo fetch action is done, we check if we can cd into the repo
   5. Each action has defined what to do in case verify fails: in this case we want to retry fetching, if it makes sense.
      1. In effect, the next Action could be the same action to repeat, or the next action in the pipeline
      2. Should we modify 
   6. Output the location of the repo created
5. Next action is to find documentation in the project. 
   1. Verify the action by making sure the files exist





new Action:
   Context: Is it just running thread? or metadata?
   Action Output: Some sort of Reporter to report what happened.
   Verifier:
      Pass Condition:
      Pass Action:
         Action Inputs: Context, Action Output, Verifier Output 
      Fail Action:
         Action Inputs: Context, Verifier Output


[[CommandReport(success=True, insights='The output indicates that the git clone command completed successfully'),
  CommandReport(success=True, insights='with all objects and deltas received and resolved.')],
 [CommandReport(success=True, insights='The installation of the nodestream package was successful without any errors.'), 
  CommandReport(success=True, insights='The project was successfully created and the command completed without errors'), 
  CommandReport(success=True, insights='The pipeline ran successfully without any errors although it did note that no targets were provided.')],
 [CommandReport(success=False, insights='The clone operation failed because the destination path already exists and is not empty.'),
  CommandReport(success=True, insights='All required packages for nodestream are already installed and no errors occurred during the process.'),
  CommandReport(success=False, insights='The command failed because the specified directory already exists.'),
  CommandReport(success=False, insights='The output does not provide enough information to determine the success or failure of the commands.'),
  CommandReport(success=False, insights='The output indicates that the pipeline ran without writing to any targets due to a lack of provided targets.')],
 [CommandReport(success=False, insights='The clone operation failed because the destination directory already exists and is not empty.'),
  CommandReport(success=True, insights='The installation process completed successfully with all requirements already satisfied.'),
  CommandReport(success=False, insights='The operation failed because the directory "my_project" already exists.'),
  CommandReport(success=False, insights="The process failed because the required file 'nodestream.yaml' does not exist.")],
 [CommandReport(success=True, insights='The nodestream package was successfully uninstalled without any errors.')]]