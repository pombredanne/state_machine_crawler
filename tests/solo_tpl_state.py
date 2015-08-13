from state_machine_crawler import transition

from . import cases


class SoloTplState(cases.State):

    @transition(source_state="LaunchedState")
    def there(self):
        pass

    @transition(target_state="LaunchedState")
    def back(self):
        pass
