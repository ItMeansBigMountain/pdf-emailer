from utils import *

# INIT LLM VARIABLES
audience = "seasoned martial artists"
stats = "supplements have changed the game for athletes, improving recovery and performance. research on testosterone boosters shows they can increase muscle mass and strength, especially in older adults. however, the effectiveness of these supplements can vary based on individual factors and the specific product used."
provider = "openai"
model = None
temperature = float(0.7)

# INIT LLM OBJECT
llm = initialize_llm(provider=provider, model_name=model, temperature=temperature)
chain = prompt_template | llm


# GENERATE NEWSLETTER CONTENT
raw_output = chain.invoke({"audience": audience, "stats": stats})
if "Subject:" in raw_output and "Body:" in raw_output:
    subject = raw_output.split("Subject:")[1].split("Body:")[0].strip()
    body = raw_output.split("Body:")[1].strip()
else:
    subject, body = "Newsletter Template", raw_output.strip()



# PRINT RESULTS
print("Generated Newsletter:")
print(subject, body)