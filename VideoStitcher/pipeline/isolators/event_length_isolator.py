###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

from typing import Dict, List
from rhombus_types.human_event import HumanEvent
from rhombus_environment.environment import Environment

def isolate_events_from_length(events: Dict[int, List[HumanEvent]]) -> Dict[int, List[HumanEvent]]:
    """Isolates events and only returns events that have a minimum number of events

    :param events: A map of objectID to human event list
    :return: Returns only events that have at least `Environment.get().minimum_event_length` events
    """

    # Loop through all of the events
    for id in list(events.keys()):
        es = events[id]

        # If the number of events does not pass the threshold, then delete them
        if len(es) < Environment.get().minimum_event_length: 
            del events[id]

    return events

