import osc.conf

from oscqam.fields import ReportFields
from oscqam.formatters import TabularOutput, VerboseOutput
from oscqam.reject_reasons import RejectReason
from oscqam.remotes import RemoteFacade


class Common:
    SUBQUERY_QUIT = 4

    all_columns_string = ", ".join(str(f) for f in ReportFields.all_fields)
    all_reasons_string = ", ".join(r.flag for r in RejectReason)

    def set_required_params(self, args):
        self.apiurl = args.apiurl
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if hasattr(args, "user") and args.user:
            self.affected_user = args.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    def list_requests(self, action, tabular, keys):
        listdata = action()
        formatter = TabularOutput() if tabular else VerboseOutput()
        if listdata:
            print(formatter.output(keys, listdata))

    @staticmethod
    def yes_no(question: str, default: str = "no") -> bool:
        if default not in ("yes", "no"):
            raise ValueError("Default must be 'yes' or 'no'")
        valid = {"y": True, "yes": True, "n": False, "no": False}
        if default == "yes":
            default = "y"
            prompt = "[Y/n]"
        else:
            default = "n"
            prompt = "[y/N]"
        while True:
            answer = input(" ".join([question, prompt])).lower()
            if not answer:
                return valid[default]
            elif valid.get(answer, None) is not None:
                return valid[answer]
            else:
                print("Invalid choice, please use 'yes' or 'no'")

    @classmethod
    def query_enum(cls, enum, tid, desc):
        """Query the user to specify one specific option from an enum.

        The enum needs a method 'from_id' that returns the enum for
        the given id.

        :param enum: The enum class to query for

        :param id: Function that returns a unique id for a enum-member.
        :type id: enum -> object

        :param desc: Function that returns a descriptive text
                for a enum-member.
        :type id: enum -> str

        :returns: enum selected by the user.

        """
        ids = [tid(member) for member in enum]
        for member in enum:
            print("{0}. {1}".format(tid(member), desc(member)))
        print("q. Quit")
        user_input = input(
            "Please specify the options (separate multiple values with ,): "
        )
        if user_input.lower() == "q":
            return cls.SUBQUERY_QUIT
        numbers = [int(s.strip()) for s in user_input.split(",")]
        for number in numbers:
            if number not in ids:
                print("Invalid number specified: {0}".format(number))
                return cls.query_enum(enum, tid, desc)
        return [enum.from_id(i) for i in numbers]
