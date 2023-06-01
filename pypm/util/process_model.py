# pypm.util.process_model


class Resources(object):
    def __init__(self):
        self._names = {}  # names: name -> id
        self._ids = {}  # ids: id -> name
        self._count = {}  # ids: id -> name

    def add(self, name, count):
        i = len(self._names)
        self._names[name] = i
        self._ids[i] = name
        self._count[i] = count

    def load(self, data):
        assert type(data) is dict
        for name in data:
            assert name not in self._names, "Resource {} already defined".format(name)
            count = None if data[name] is None else int(data[name])
            self.add(name, count)

    def __len__(self):
        """Return the number of resources in the model."""
        return len(self._names)

    def __iter__(self):
        """Return a generator for the resource names."""
        for key in self._names:
            yield key

    def count(self, name):
        return self._count[self._names[name]]


class ProcessModel(object):
    """
    An object that represents the data in a process model.

    Args
    ----
    data : dict, Default: {}
        A dictionary that is used to initialize this object.
    """

    def __init__(self, data={}):
        self.resources = Resources()
        self.hours_per_timestep = 1
        self._activities = {}  # activities: int_id -> activity
        self._names = {}  # names: name -> int_id
        if len(data) > 0:
            self.load(data)

    def load(self, data):
        """Load the process model from YAML/JSON data."""
        tmp = set(["resources", "activities"])
        assert tmp.issubset(
            set(data.keys())
        ), "Expected data with 'resources' and 'activities'"
        self.resources.load(data["resources"])
        for activity in data["activities"]:
            self._add_activity(activity)
        self.hours_per_timestep = data.get('hours_per_timestep',1)
        self._initialize()

    def __len__(self):
        """Return the number of activities in the model."""
        return len(self._activities)

    def __iter__(self):
        """Return a generator for the activity names."""
        for key in self._names:
            yield key

    def __getitem__(self, name_or_id):
        """Return an activity given its name or id."""
        if isinstance(name_or_id, int):
            return self._activities[name_or_id]
        return self._activities[self._names[name_or_id]]

    def id(self, name):
        return self._names[name]

    def _add_activity(self, activity):
        """Add the activity object to the process model."""
        assert "name" in activity, "Missing 'name' in activity"
        assert (
            activity["name"] not in self._names
        ), "Activity name {} already defined".format(activity["name"])
        i = len(self._names)
        activity["id"] = i
        self._names[activity["name"]] = i

        assert activity.get("max_delay",None) is None, "Use of 'max_delay' is disallowed.  Use 'delay_after_hours'."
        if activity.get("delay_after_hours", None) is not None:
            activity["delay_after_timesteps"] = activity["delay_after_hours"]
            del activity["delay_after_hours"]
        if activity.get("delay_after_timesteps", None) is None:
            activity["delay_after_timesteps"] = None

        if "max_hours" in activity["duration"]:
            activity["duration"] = {
                "max_timesteps": activity["duration"]["max_hours"],
                "min_timesteps": activity["duration"]["min_hours"],
            }
        self._activities[i] = activity
        if activity.get("resources", None) is None:
            activity["resources"] = {}
        else:
            assert type(activity["resources"]) is dict
            #
            # Default value is to use one copy of each resource
            #
            for key in activity["resources"]:
                if activity["resources"][key] is None:
                    activity["resources"][key] = 1
        #
        # WEH - Should we adopt the term 'predecessor'?
        #
        if activity.get("dependencies", None) is None:
            activity["dependencies"] = []

    def _initialize(self):
        """Initialize derived data from core process model representation."""

    def data(self):
        resources = {name: None for name in sorted(self.resources)}
        activities = []
        for name in self:
            ans = {}
            ans["name"] = name
            ans["delay_after_timesteps"] = self[name]["delay_after_timesteps"]
            ans["dependencies"] = self[name]["dependencies"]
            ans["resources"] = self[name]["resources"]
            ans["duration"] = self[name]["duration"]
            activities.append(ans)
        return dict(resources=resources, activities=activities, hours_per_timestep=self.hours_per_timestep)
