Benefits of Using Pydantic:
------------------------------------------------------------------------------------------------
- Zero Boilerplate design: No need to create __init__(), Getter [@property] and Setter [<function>.setter] validations. Pydantic will generate them automatically
- Data Type Validation and conversion: If a variable defined as int and if user passes string ("500"), then pydantic will automatically convert that string to int instead of crasing
- Comprehensive Error reporting: if all fields are invalid then pydantic will catches the error and return the details in JSON format rather than crasing at first invalid field


Important Pydantic Classes:
[1] BaseModel: provides base class abstraction with '__init__()' constructor
    Few important functions:
    - model_dump() : Converts your live python object into a standard dictionary
    - model_dump_json() : Converts your live python object into JSON string
    - model_validate(data_dict) : Takes a raw dictionary and instantly transforms it into a verified object

[2] Field : You use 'Field()' inside a BaseModel to assign metadata, validation boundaries, defaults and aliases.
    Key arguments:
    - default : Defines what value will be considered if no value passed
    - default_factory : Accepts a function to generate 'default' value dynamically. Ex: default_factory=datetime.now()
    - alias : Allows you to map a different named incoming data key

[3] EmailStr : To perform email validation. You must need to install 'pydantic[email]' package.

[4] @field_validator: Targeted value check point. Run custom functions or external module checks on one field. Useful when we need to perform custom valiation on a specific field which is not default data type in python. This acts like a hook between the data field and the validation function
    Key arguments:
    - field_name : A String matching the exact variable you want to validate. You can pass multiple fields if they share the same rule

    - mode
        - after(default) : Runs after Pydantic performs the basic checks and type conversion
        - before : Runs on the raw user input before pydantic touches it.

[5] @model_validator : Multi-Field Cross Examination, when validation relies on comparison of two or more fields together


@classmethod and 'cls' : 'cls' with @classmethod only when your function needs to be build an abstraction layer

self : when we need to make changes at the object level. (check Example - 3 for understanding.)


(**) - Built-in Python operator called 'Dictionary Unpacking Operator'. Without this we might need to extract every line of a dictionary manually
Ex:
ai_payload = {
    "engine": "google",
    "search_query": " 'Python Pydantic v2 tutorial'",
    "timeout_seconds": 10
}

With (**): Consider AgentSearchToolCall is a defined class contains "engine", "search_query", "timeout_seconds"

tool_call = AgentSearchToolCall(**ai_payload) => Python will automatically unpack the dictionary

without (**): We need to unpack it manually
tool_call = AgentSearchToolCall(
    engine=ai_payload["engine"],
    search_query=ai_payload["search_query"]
    timeout_seconds=ai_payload["timeout_seconds"]
)

(*) - is used to unpack sequential iterables like Lists or Tuples


Useful Functions:
[1] model_dump_json(indent=2) : Convert Class output to JSON
print(inc1.model_dump_json(indent=2))

[2] ConfigDict: To force any data passed to class converting to upper case or lower case
Ex:
from pydantic import ConfigDict, BaseModel
class Incident(BaseModel):
    # To converting to lower case
    model_config = ConfigDict(str_to_lower=True) 

    ticket_id: str
    priority: str

    # To converting to upper case
    model_config = ConfigDict(str_to_upper=True)

[3] Converting a single field using 'Annotated' and 'StringConstraints'

from typing import Annotated
from Pydantic import BaseModel, StringConstraints

class Incident(BaseModel):
    # Forcing ticket_id only to convert into lower case
    ticket_id: Annotated[str, StringConstraints(to_lower=True)]
    priority: str


------------------------------------ Working with Environment Files --------------------------------
Using Pydantic to read '.env' file to load environment variables securely.
Intent - Store DB Password, API Secrets into '.env' file. Pydantic-settings library lets you read these files automatically and converts strings into proper data types (like text to integer)
We will use two specific classes named 'BaseSettings' and 'SettingsConfigDict' into this demo

[For details check 4-Pydantic-dot-env-parsing.ipynb]

Here we will use below classes for various purposes along with 'Field' class to load environment variables

We need to import below libraries:

from pydantic import Field, SecretStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


[a] Our class must inherit from 'BaseSettings' class
    ex: class AppConfig(BaseSettings):

[b] To load the '.env' file we will use 'SettingsConfigDict' class

    model_config = SettingsConfigDict(
        env_file= base_dir / '.env',               # Will look for this specific file name
        env_file_encoding='utf-8',     # Read text using universal encoding
        extra='ignore'                 # Ignore other variables in the system env
    )


[c] SecretStr = To load any secret stored inside the '.env' file like DB Password or API token
    Ex: cloud_access_token: SecretStr = Field(alias="CLOUD_ACCESS_TOKEN")

    Here 'CLOUD_ACCESS_TOKEN' contains the API token
    
    this class will load the secret and will display in masked way '*********'

[d] We can load or extract the Secrets if needed in plain text format as well by using 'get_secret_value()' function
    example: config.cloud_access_token.get_secret_value()


[e] Dynamically load the environment file:
import os
import sys

target_profile = "dev" # default

if len(sys.argv) > 1:
   argument = sys.argv[1].strip().lower()
   if argument in ["dev", "prd"]:
      target_profile = argument
   else:
      print(f"⚠️ Warning: Unknown profile '{sys.argv[1]}'. Defaulting to 'dev'.")

target_env_file = f"{target_profile}.env"

try:
  # For simple python file
  base_dir = Path(__file__).resolve().parent
except NameError:
  base_dir = Path(os.getcwd())

Executing from terminal:
#python3 app_launcher.py dev



------------------------------ Working with Pydantic and Mocking Tools API calls ------------------
In this program we will create dummy 'tools' and will call them as API calling




------------------------------ MCP [Model Context Protocol] ------------------------------------
Core Concepts of MCP:
- Client-Server Architecture
- Often compared with USB-Type-C connector which gives a single interface for various types of devices to connect. Here in Agentic-AI world, instead of using multiple API's to connect with multiple applications, we are using MCP [Connecting to DB, Executing some script/playbooks, websearch]
- MCP Servers can also be think like a restuarant who has 'Menus' [in Agentic-AI world called 'Schemas'] and 'Kitchen' [In Agentic-AI world called functions]. Where clients read the menus and places an order.
- Uses JSON-RPC 2.0 communication layer for schema discovery and functional execution (text based universal format uses standardized dictionaries containing 'jsonrpc', 'id', 'method', 'params')


Core Components:
- Server: Light-weight program that acts like a bridge between your AI and your data (loca files , Google Drive, Company Databases, Knowledge bases) which might require different connecting methods or API calls.
- Client: AI Application wants to use those data
- Protocol: The universal set of rules that can be used to setup the bridge easily



--------------------------- Converting Jupyter Notebook files to Python Scripts --------------------
#uv pip install nbconvert
#jupyter nbcovert --to script [<your_notebook_name.ipynb> | *.ipynb]