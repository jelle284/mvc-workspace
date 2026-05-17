## MVC Workspace
Workspace manager and GUI for interacting with "Mini Version Control" (MVC).

![Alt text](resources/dock_widget.png)
### Use
- When using the first time, open the settings button to configure your base path and user name.
    - Set the base path to where you want your project files to be stored.
- Use the browse button to select your workspace directory, where your FreeCAD files are.
- If the workspace does not have an active project, use the 'Create Project' or 'Load' buttons to set one.
- When the workspace has an active project, use the file browser to check or uncheck files, and then the 'submit' button to add or update files in the project.
- The 'Collect' button will take the files from the active project and add them to your workspace.

For additional information about commands, see the [MVC repository](https://github.com/jelle284/mvc) 

### Workflow example
- An assembly is kept as seperate files and stored in an MVC project.
- One or more users updates parts and submit the files when they are done.
- A single user collects all the files submitted and reviews the assembly.
- When the review is passed, the submits are accepted.
- When the design is final, the project is released for as-built documentation.

#### About Colors
- Black means files are up-to-date.
- Orange means files have changed.
- Green means files are claimed by you.
- Red means files are claimed by other users.
- Blue means file is not in the project.
