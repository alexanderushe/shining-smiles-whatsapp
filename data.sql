--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: student_contacts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.student_contacts (id, student_id, firstname, lastname, student_mobile, guardian_mobile_number, last_updated, preferred_phone_number, email, address, preferred_contact_method, emergency_contact_name, emergency_contact_number, preferred_language, verification_code) FROM stdin;
1	SSC20257279	Peace	Kuwaza	+263711206287	+263711206287	2025-06-27 11:13:11.912912	+263711206287	\N	\N	\N	\N	\N	en	\N
\.


--
-- Data for Name: gate_passes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.gate_passes (id, student_id, pass_id, issued_date, expiry_date, payment_percentage, whatsapp_number, last_updated, pdf_path, qr_path) FROM stdin;
\.


--
-- Name: gate_passes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.gate_passes_id_seq', 6, true);


--
-- Name: student_contacts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.student_contacts_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

