
CREATE DATABASE stream;

CREATE TABLE "clicks" (
  "id" serial UNIQUE PRIMARY KEY NOT NULL,
  "session_id" text,
  "event_name" varchar(20),
  "event_id" text NOT NULL,
  "traffic_source" varchar(15),
  "product_id" integer,
  "quantity" integer,
  "item_price" float,
  "payment_status" varchar(15),
  "search_keywords" varchar(50),
  "promo_code" varchar(20),
  "promo_amount" float,
  "created_at" date DEFAULT (now())
);

CREATE TABLE "transactions" (
  "id" serial UNIQUE PRIMARY KEY NOT NULL,
  "customer_id" text,
  "booking_id" text,
  "session_id" text,
  "payment_method" varchar(50),
  "payment_status" varchar(15),
  "promo_amount" float,
  "promo_code" varchar(20),
  "shipment_fee" float,
  "shipment_location_lat" text,
  "shipment_location_lon" text,
  "total_amount" float,
  "product_id" integer,
  "quantity" integer,
  "item_price" float,
  "created_at" date DEFAULT (now())
);
