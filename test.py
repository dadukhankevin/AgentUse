import agentuse
import multiprocessing
import time

# Multiple agents in parallel using multiprocessing
def task1():
    agentuse.run("create a web scraper", cli_cmd="claude")

def task2():
    # Small delay to avoid window creation conflicts
    time.sleep(3)
    agentuse.run("craft a clever rick roll and then use it", cli_cmd="gemini")

if __name__ == "__main__":
    # Use multiprocessing instead of threading to avoid OpenAI client conflicts
    p1 = multiprocessing.Process(target=task1)
    p2 = multiprocessing.Process(target=task2)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()