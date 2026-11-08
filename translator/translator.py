class ListedField:
    def __init__(
        self, field, name, type_, value, returnType, parameters):
        
        self.field = field
        self.name = name
        self.type_ = type_
        self.value = value
        self.returnType = returnType,
        self.parameters = parameters


# (&str)var title : "Verison"
verison_field = ListedField(
    field= "const",
    name= "TITLE",
    type_= "&str",
    value= '"Verison"',
)

rust_field = ListedField(
    field= "",
    name= "",
    type_= "",
    value= "",
)

def TranslateFieldToRust(field: ListedField):
    
    if verison_field.field == "var":
        rust_field.field = "let mut"
    elif verison_field.field == "const":
        rust_field.field = "const"
    
    rust_field.name = field.name
    rust_field.value = field.value
    rust_field.type_ = field.type_

    print (
    rust_field.field,
    rust_field.name,":",
    rust_field.type_,"=",
    rust_field.value,";"
    )

TranslateFieldToRust(verison_field)

# GOAL:
# let mut title : &str = "Verison";