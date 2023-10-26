# BRMM_webapp

## Web application structure
 Each block has 3 sections , first line is HTML page, second is route and third is data passed in to the html page.

![image](https://github.com/Alex-Beep-Cao/BRMM_webapp/assets/65649144/6b06a170-a831-4ccb-8a0c-1d2bd9bc1223)


## Assumptions
1. We don't have a defined age threshold. We need a cutoff date to calculate the participants' ages.
2. We can't ascertain the accuracy of the age provided by each individual, so when entering the information into the computer, we need to verify the ID of each participant.

## Design decisions
In this project, I have utilized three main HTML bases: base, admin, and message. The base page is primarily used for the driver interface, including functionalities like listing courses and displaying driver run details. Many default functions are inherited from this page.
The admin page is primarily designed for the admin interface, and it inherits functions for adding, updating, and searching information. 
The message page serves the purpose of providing correct feedback when the admin updates or adds information, such as successful additions or various errors. Different errors will result in the display of corresponding error messages.

I used the method of page inheritance in this project because it offers numerous advantages.
For example： 
1. Code Reusability: You can abstract shared HTML structure and styles into a base template and then inherit this base template in other pages, reducing code redundancy and improving code maintainability.
2. Consistency and Style: By using page inheritance, you can ensure a consistent style and layout across the entire application. This helps provide a better user experience as users will find the application familiar throughout.
3. Easier Maintenance: If you need to change the overall look and layout of the application, you only need to make modifications in the base template, without the need to change every individual page. This reduces maintenance costs and the risk of errors.
4. Increased Development Efficiency: By reducing the need to write repetitive HTML code, page inheritance can improve development efficiency and shorten development time.
Flask page inheritance helps create a consistent, maintainable, and efficient web application while reducing code redundancy and the chance of errors.

## Database question
o What SQL statement creates the car table and defines its three fields/columns? (Copy and paste the relevant lines of SQL.)
- CREATE TABLE IF NOT EXISTS car
(
car_num INT PRIMARY KEY NOT NULL,
model VARCHAR(20) NOT NULL,
drive_class VARCHAR(3) NOT NULL
);

o Which line of SQL code sets up the relationship between the car and driver tables?
-FOREIGN KEY (caregiver) REFERENCES driver(driver_id)

o Which 3 lines of SQL code insert the Mini and GR Yaris details into the car table?
-INSERT INTO car VALUES
(11,'Mini','FWD'),
(17,'GR Yaris','4WD');

o Suppose the club wanted to set a default value of ‘RWD’ for the driver_class field. What specific change would you need to make to the SQL to do this? (Do not implement this change in your app.)
-Update car Set drive_class = 'RWD';

o Suppose logins were implemented. Why is it important for drivers and the club admin to access different routes? As part of your answer, give two specific examples of problems
that could occur if all of the web app facilities were available to everyone.
-1. Data Privacy and Security Concerns： If administrators and participants use the same route, there is a possibility of information leakage, which could lead to unfair competition.
-eg: driver don't need to have search function, add or update function if they do, they might update their own score, which is not fair.
   
-4. Operational Chaos: When all users have access to all web application functionalities, it can potentially lead to operational chaos. Drivers and club administrators have distinct roles and responsibilities, requiring specific tools to support their tasks.
-eg: drivers only need to see their score and overall result, but admin needs have update, add .... functions to manage the event.
