# ADR
## ADR-001: Deploy as a static web application.
As I tried installing the SW as a python package in a user's environment,
it overwhelmed the user.

Even though command interface is much faster/easier to use (at least for myself),
GUI had more advantages than disadvantages.

Here are the advantages/disadvantages I have found.

### Advantages
- Easy to deploy, i.e. github docs is enough.
- Easy to try-out for a user.
- Easy to explain how to use it. (GUI explains itself)
- Users don't have to worry about updating the application and dependencies.
- GUI is relatively easy to implement since web browsers provide lots of useful GUI components/interfaces.
- Relatively secure than directly accessing to the users file system.

### Disadvantages
- More things to consider due to browser cacheing/storage layers (could be an advantage.)
    > Could be an advantage for securely/effectively maintaining configuration files and user inputs.
- Users have to upload files themselves.
    > After UX testing with a user, it was much less of an effort compared to opening a terminal and activating a virtual environment.
- Slower (loading is significantly slower since it downloads all the dependencies every time.)
    > The performance is not really a problem since it is only for small-businesses
    who have less than thousands of orders a day. 
    
    > Also, slow-feedback from the program gives users good time to process what is happening compared to fast-logging in a terminal.

As a result, I decided to keep the program as a **static-web application** instead of a command line based program.
