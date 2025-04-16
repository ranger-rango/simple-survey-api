CREATE DATABASE IF NOT EXISTS sky_survey_db;

use sky_survey_db;

CREATE TABLE IF NOT EXISTS personal_information(
    email_address VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    gender  ENUM("MALE", "FEMALE", "OTHER") NOT NULL,
    PRIMARY KEY (email_address)
);

CREATE TABLE IF NOT EXISTS resume_information(
    resume_id INT NOT NULL AUTO_INCREMENT,
    email_address VARCHAR(100) NOT NULL,
    description_ TEXT NOT NULL,
    programming_stack TEXT NOT NULL,
    PRIMARY KEY (resume_id),
    FOREIGN KEY (email_address) REFERENCES personal_information(email_address)
);

CREATE TABLE IF NOT EXISTS certificates(
    certificate_id VARCHAR(50) NOT NULL,
    resume_id INT NOT NULL,
    certificate_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (certificate_id),
    FOREIGN KEY (resume_id) REFERENCES resume_information(resume_id)
);