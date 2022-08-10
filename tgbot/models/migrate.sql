CREATE TABLE promo_code (
    code VARCHAR NOT NULL, 
    "user" BIGINT, 
    amount_use INTEGER, 
    discount_size INTEGER, 
    PRIMARY KEY (code), 
    FOREIGN KEY("user") REFERENCES users (id) ON DELETE CASCADE
);
