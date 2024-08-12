from typing import List
from scripts.utility import HERB_DICT


class Territory:
    """Represents one location on the clan's territory."""

    def __init__(self,
                 key:str,
                 name:str,
                 description:str,
                 tags:List[str],
                 herbs:List[str],
                 prey_quality:int,
                 is_contested:bool=False,
                 owned_by:str=None,
                 camp_type:str=None
                 ) -> None:
        self.key:str = key
        self.name:str = name
        self.description:str = description
        self.tags:List[str] = tags
        self.herbs:List[str] = herbs
        self.prey_quality:int = prey_quality
        self.camp_type:str = camp_type
        self.owned_by:str = owned_by
        self.is_contested = is_contested


    def can_patrol(self, patrol_type:str) -> bool:
        if self.tags is None or len(self.tags) == 0:
            return False

        if patrol_type == "hunting":
            return "hunting" in self.tags


    def get_description(self, patrol_type:str):
        """Get the full description text to display."""
        desc_lines = []

        if self.is_contested:
            if self.owned_by is not None:
                desc_lines.append("This location has been lost to o_n. Send a border patrol here to attempt to reclaim it.")
            else:
                desc_lines.append("This location is not currently under c_n's control.")

        desc_lines.append(self.description)

        if self.herbs is not None and len(self.herbs) > 0:
            herb_names = [HERB_DICT["names"][herb] for herb in self.herbs]
            herb_list = array_to_list(herb_names)
            desc_lines.append(f"Some herbs can be found here: {herb_list}.")

        desc_lines.append(get_prey_quality_str(self.prey_quality))

        # if self.has_tag("stressful"):
        #     desc_lines.append("Patroling here will be stressful.")
        # if self.has_tag("relaxing"):
        #     desc_lines.append("Patroling here will be relaxing.")

        return '\n\n'.join(desc_lines)


    def has_tag(self, tag_name) -> bool:
        if self.tags is not None and len(self.tags) > 0:
            return tag_name in self.tags
        return False



# def parse_strings(strs:List[str]) -> List[str]:
#     result = []
#     for line in strs:
#         line = line.replace('o_n')

def get_prey_quality_str(prey_quality:int) -> str:
    # TODO: this should be saved in json somewhere
    if prey_quality <= 0:
        return "Prey cannot be found here."
    if prey_quality == 1:
        return "Very small amounts of prey can be found here."
    if prey_quality == 2:
        return "A small amount of prey can be found here."
    if prey_quality == 3:
        return "Some prey can be found here."
    if prey_quality == 4:
        return "A good amount of prey can be found here."
    if prey_quality >= 5:
        return "Prey is abundant here."

# TODO: move.
def array_to_list(list) -> str:
    result = ""
    for i in range(0, len(list)):
        if i == 0:
            result += list[i]
        elif (i == len(list) - 1):
            result += ", and " + list[i]
        else:
            result += ', ' + list[i]

    return result