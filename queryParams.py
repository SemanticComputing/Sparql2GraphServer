from dataclasses import dataclass
from networkbuilder import NetworkBuilder
from typing import Dict, Union

@dataclass(eq=False)
class QueryParams:
    endpoint:str
    nodes: str
    links: str
    prefixes:str                = ''
    limit:int                   = 1000
    id:str                      = None
    optimize:float              = 1.0
    format:str                  = NetworkBuilder.CYTOSCAPE
    log_level:Union[int, str]   = 10
    removeMultipleLinks:bool    = True
    customHttpHeaders:Dict      = None
    adjust_layout:bool          = False

    def __post_init__(self):
        self.limit = int(self.limit)
        self.optimize = float(self.optimize)
