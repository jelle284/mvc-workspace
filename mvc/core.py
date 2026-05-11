import os
from pathlib import Path
import shutil
from datetime import datetime

from mvc.helpers import MVCError, Version, Project, Workspace, FileID, get_submit_path, get_stable_path, get_release_path, list_files_dir

class MiniVC:
    def __init__(self, base_path: str, user_path: str, user_name: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise MVCError("Invalid base path.")
        self.user_path = Path(user_path)
        if not self.user_path.exists():
            raise MVCError("Invalid user path.")
        self.user_name = user_name
        
    def _write_changelog(self, project: Project):
        md = []
        project_path = self.base_path / project.name
        if project.id.dev > 0:
            md.append(f"# development version")
        for i in range(project.id.dev, 0, -1):
            version_path = project_path / get_submit_path(i)
            version = Version.load(version_path)
            for line in version.description:
                md.append(line)
        
        if project.id.minor > 0:
            md.append(f"# stable version")
        version_path = project_path / get_stable_path()
        version = Version.load(version_path)
        for line in version.description:
            md.append(line)
        
        if project.id.major > 0:
            md.append(f"# Release version")
        for i in range(project.id.major, 0, -1):
            version_path = project_path / get_release_path(i)
            version = Version.load(version_path)
            for line in version.description:
                md.append(line)

        filename = self.user_path / "changelog.md"
        with open(filename, 'w') as fd:
            for line in md:
                fd.write(line + "\n")

    def _current_timestamp(self) -> str:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
    def _file_walker(self, project: Project, file_id: FileID) -> dict[str, Path]:
        ret_files = {}
        version_path = self.base_path / project.name / file_id.sub_path
        version = Version.load(version_path)
        version_files = list_files_dir(version_path)
        for file in version_files:
            ret_files[file] = version_path
        for file, include_id in version.include.items():
                file_path = self.base_path / project.name / include_id.sub_path
                ret_files[file] = file_path
        return ret_files
    
    def create(self, name: str):
        if name == '': raise MVCError("Project must have a name.")
        id = FileID(0,0,0)
        project = Project(
            name,
            id,
            {})
        project_path = self.base_path / name
        try:
            os.makedirs(project_path)
        except OSError:
            raise MVCError("Trying to create project which already exists.")
        project.save(project_path)
        version = Version(
            [f"## {id}",
             f"{name} was created",
             self._current_timestamp()],
            {})
        version_path = project_path / id.sub_path
        os.makedirs(version_path, exist_ok=True)
        version.save(version_path)
        workspace = Workspace(
            name,)
        workspace.save(self.user_path)

    def load(self, name: str):
        project_path = self.base_path / name
        project = Project.load(project_path)
        workspace = Workspace(
            project.name,)
        workspace.save(self.user_path)
    
    def submit(self, files: list[str], comment: str = ""):
        if not files:
            raise MVCError("Files is empty.")
        user_files = list_files_dir(self.user_path)
        if any(file not in user_files for file in files):
            raise MVCError("File does not exist in workspace.")
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        for file in files:
            if file in project.claims:
                if project.claims[file] != self.user_name:
                    raise MVCError("One or more files have been claimed by other user")
        version_path = project_path / project.id.sub_path
        version = Version.load(version_path)
        work_files = list_files_dir(version_path)
        for file in work_files:
            version.include[file] = FileID.copy(project.id)
        for file in files:
            version.include.pop(file, None)
        project.id.dev += 1
        version_path = project_path / project.id.sub_path
        os.makedirs(version_path, exist_ok=True)
        for file_name in files:
            src_path = self.user_path / file_name
            dst_path = version_path / file_name
            shutil.copy2(src_path, dst_path)

        version.description = [f"## {project.id}"]
        if comment: version.description.append(comment)
        version.description +=  [f"Submitted files:",
                               *[f' + {file}' for file in files]]
        version.save(version_path)
        project.save(project_path)

    def remove(self, files: list[str], comment: str = ""):
        if not files:
            raise MVCError("Files is empty.")
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        project_files = self._file_walker(project, project.id)
        if any(file not in project_files for file in files):
            raise MVCError("File does not exist in project.")
        for file in files:
            if file in project.claims:
                if project.claims[file] != self.user_name:
                    raise MVCError("One or more files have been claimed by other user")
        version_path = project_path / project.id.sub_path
        version = Version.load(version_path)
        work_files = list_files_dir(version_path)
        for file in work_files:
            version.include[file] = FileID.copy(project.id)
        for file in files:
            version.include.pop(file, None)
        project.id.dev += 1
        version_path = project_path / project.id.sub_path
        os.makedirs(version_path, exist_ok=True)
        version.description = [f"## {project.id}"]
        if comment: version.description.append(comment)
        version.description +=  [f"Submitted files:",
                               *[f' - {file}' for file in files]]
        project.save(project_path)
        version.save(version_path)
        
    def accept(self, comment: str = ""):
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        if project.id.dev == 0:
            raise MVCError("No files submitted")
        submits_to_collect = project.id.dev
        dev_path = project_path / get_submit_path(submits_to_collect)
        dev_version = Version.load(dev_path)
        dev_files = list_files_dir(dev_path)
        stable_path = project_path / get_stable_path()
        stable_version = Version.load(stable_path)
        stable_files = list_files_dir(stable_path)
        check_files = dev_files + [k for k in dev_version.include]
        for file in check_files:
            stable_version.include.pop(file, None)
        rm_files = [f for f in stable_files if f not in check_files]
        for file in rm_files:
            os.remove(stable_path / file)
        for file in dev_files:
            src_path = dev_path / file
            shutil.copy2(src_path, stable_path)
        for file, file_id in dev_version.include.items():
            src_path = project_path / file_id.sub_path / file
            if file_id.dev > 0:
                shutil.copy2(src_path, stable_path)
            elif file_id.minor == 0 and file_id.major > 0:
                stable_version.include[file] = file_id
        project.id.minor += 1
        project.id.dev = 0
        sub_description = [f"## {project.id}",
                           comment,]
        for i in range(submits_to_collect, 0, -1):
            sub_version_path = project_path / get_submit_path(i)
            sub_version = Version.load(sub_version_path)
            sub_description += sub_version.description
            sub_description.append("")
        stable_version.description = sub_description + stable_version.description
        stable_version.save(stable_path)
        temp_path = project_path / "temp"
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        project.save(project_path)

    def release(self, comment: str = ""):
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        if project.id.dev > 0:
            raise MVCError("Unsaved submits.")
        if project.id.minor == 0:
            raise MVCError("No new files to release.")
        version_path = project_path / project.id.sub_path
        version = Version.load(version_path)
        project.id.major += 1
        project.id.minor = 0
        description = [f"## {project.id}",
                       comment,]
        version.description = description + version.description
        version.save(version_path)
        next_version = Version([], {})
        ref_files = os.listdir(version_path)
        ref_files.remove(".mvc")
        for file in ref_files:
            next_version.include[file] = project.id
        release_path = project_path / project.id.sub_path
        shutil.move(version_path, release_path)
        os.makedirs(version_path)
        next_version.save(version_path)
        project.save(project_path)

    def collect(self, file_id: FileID):
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        if (project.id.dev < file_id.dev or
            project.id.minor < file_id.minor or
            project.id.major < file_id.major):
            raise MVCError("Invalid argument!")
        files_to_add = self._file_walker(project, file_id)
        for file in files_to_add:
            file_path = Path(files_to_add[file]) / file
            shutil.copy2(file_path, self.user_path)
        self._write_changelog(project)
    
    def available(self) -> list[FileID]:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        ret = []
        for i in range(project.id.dev, 0, -1):
            ret.append(FileID(project.id.major, project.id.minor, i))
        if project.id.minor > 0:
            ret.append(FileID(project.id.major, project.id.minor, 0))
        for i in range(project.id.major, 0, -1):
            ret.append(FileID(i, 0, 0))
        return ret
    
    def list_projects(self) -> dict[str, str]:
        projects_paths = os.listdir(self.base_path)
        ret = {}
        for path in projects_paths:
            try:
                project = Project.load(self.base_path / path)
                ret[project.name] = str(project.id)
            except FileNotFoundError: pass
        return ret

    def status(self) -> list[str]:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        if project.id.dev > 0:
            ret = []
            for i in range(project.id.dev, 0, -1):
                version_path = project_path / get_submit_path(i)
                version = Version.load(version_path)
                ret += version.description
                ret.append("")
            return ret
        elif project.id.major > 0 and project.id.minor == 0: 
            sub_path = get_release_path(project.id.major)
        else:
            sub_path = get_stable_path()
        version_path = project_path / sub_path
        version = Version.load(version_path)
        return version.description
    
    def changes(self, file_id: FileID = None) -> tuple[list[str], list[str]]:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        workspace_files = list_files_dir(self.user_path)
        if not file_id: file_id = project.id
        version_files = self._file_walker(project, file_id)
        changed_files = []
        new_files = []
        for file in workspace_files:
            fpath = self.user_path / file
            stamp = os.path.getmtime(fpath)
            if file not in version_files:
                new_files.append(file)
            else:
                version_file_path = version_files[file] / file
                version_file_stamp = os.path.getmtime(version_file_path)
                if version_file_stamp != stamp:
                    changed_files.append(file)
        return new_files, changed_files
    
    def claim(self, files: list[str]) -> None:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        contents = self._file_walker(project, project.id)
        for file in files:
            if file not in contents:
                raise MVCError("File is not contained in the project.")
            project.claims[file] = self.user_name
        project.save(project_path)
    
    def unclaim(self, files: list[str], force=False) -> None:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        for file in files:
            if file in project.claims:
                user_owns_file = project.claims[file] == self.user_name
                if user_owns_file or force:
                    project.claims.pop(file, None)
                else: raise MVCError("File was claimed by another user")
        project.save(project_path)
    
    def get_claims(self) -> dict[str,str]:
        workspace = Workspace.load(self.user_path)
        project_path = self.base_path / workspace.project
        project = Project.load(project_path)
        return project.claims