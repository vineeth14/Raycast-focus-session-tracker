import rumps
import data_access


class RaycastFocusStatusBarApp(rumps.App):
    @rumps.clicked("Test")
    def test(self, _):
        current_streak = data_access.get_current_streak()
        rumps.notification("Awesome title", "amazing subtitle", "hi!!1")


if __name__ == "__main__":
    RaycastFocusStatusBarApp("Focus").run()
