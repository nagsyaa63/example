const mysql = require('mysql');

const connection = mysql.createConnection({
    host: 'localhost',
    user: 'prabhav',
    password: 'Pbksql876',
    database: 'personal_finance'
});

connection.connect((err) => {
    if (err) {
        console.error('Error connecting to MySQL database:', err);
        return;
    }
    console.log('Connected to MySQL database');

    // Read from the expenses table and display all the expenses logged till now
    connection.query('SELECT * FROM expenses', (err, results) => {
        if (err) {
            console.error('Error reading expenses:', err);
            return;
        }
        console.log('Expenses:', results);
    });

    connection.end(); // Don't forget to close the connection when you're done
});
