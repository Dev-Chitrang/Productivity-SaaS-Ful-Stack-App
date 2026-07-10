from app.modules.tasks.enums import TaskStatus, TaskPriority


class TestTaskStatus:
    def test_todo_value(self):
        assert TaskStatus.TODO.value == "TODO"

    def test_in_progress_value(self):
        assert TaskStatus.IN_PROGRESS.value == "IN PROGRESS"

    def test_done_value(self):
        assert TaskStatus.DONE.value == "DONE"

    def test_all_members(self):
        assert set(TaskStatus) == {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE}

    def test_is_str_enum(self):
        assert issubclass(TaskStatus, str)

    def test_comparison_with_string(self):
        assert TaskStatus.TODO == "TODO"
        assert TaskStatus.IN_PROGRESS == "IN PROGRESS"
        assert TaskStatus.DONE == "DONE"


class TestTaskPriority:
    def test_low_value(self):
        assert TaskPriority.LOW.value == "LOW"

    def test_medium_value(self):
        assert TaskPriority.MEDIUM.value == "MEDIUM"

    def test_high_value(self):
        assert TaskPriority.HIGH.value == "HIGH"

    def test_all_members(self):
        assert set(TaskPriority) == {TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH}

    def test_is_str_enum(self):
        assert issubclass(TaskPriority, str)

    def test_comparison_with_string(self):
        assert TaskPriority.LOW == "LOW"
        assert TaskPriority.MEDIUM == "MEDIUM"
        assert TaskPriority.HIGH == "HIGH"
