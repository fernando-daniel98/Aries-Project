PGDMP     :    6    
        	    {            dw_censo    14.5    14.5     q           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            r           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            s           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            t           1262    71106    dw_censo    DATABASE     h   CREATE DATABASE dw_censo WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE = 'Portuguese_Brazil.1252';
    DROP DATABASE dw_censo;
                postgres    false            �            1259    71344    dim_ano_censo    TABLE     l   CREATE TABLE public.dim_ano_censo (
    pk_ano_censo integer NOT NULL,
    anocenso character varying(4)
);
 !   DROP TABLE public.dim_ano_censo;
       public         heap    postgres    false            �            1259    71343    dim_ano_censo_pk_ano_censo_seq    SEQUENCE     �   CREATE SEQUENCE public.dim_ano_censo_pk_ano_censo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 5   DROP SEQUENCE public.dim_ano_censo_pk_ano_censo_seq;
       public          postgres    false    230            u           0    0    dim_ano_censo_pk_ano_censo_seq    SEQUENCE OWNED BY     a   ALTER SEQUENCE public.dim_ano_censo_pk_ano_censo_seq OWNED BY public.dim_ano_censo.pk_ano_censo;
          public          postgres    false    229            �           2604    71347    dim_ano_censo pk_ano_censo    DEFAULT     �   ALTER TABLE ONLY public.dim_ano_censo ALTER COLUMN pk_ano_censo SET DEFAULT nextval('public.dim_ano_censo_pk_ano_censo_seq'::regclass);
 I   ALTER TABLE public.dim_ano_censo ALTER COLUMN pk_ano_censo DROP DEFAULT;
       public          postgres    false    230    229    230            n          0    71344    dim_ano_censo 
   TABLE DATA           ?   COPY public.dim_ano_censo (pk_ano_censo, anocenso) FROM stdin;
    public          postgres    false    230   M       v           0    0    dim_ano_censo_pk_ano_censo_seq    SEQUENCE SET     M   SELECT pg_catalog.setval('public.dim_ano_censo_pk_ano_censo_seq', 1, false);
          public          postgres    false    229            �           2606    71349     dim_ano_censo dim_ano_censo_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.dim_ano_censo
    ADD CONSTRAINT dim_ano_censo_pkey PRIMARY KEY (pk_ano_censo);
 J   ALTER TABLE ONLY public.dim_ano_censo DROP CONSTRAINT dim_ano_censo_pkey;
       public            postgres    false    230            n   8   x�Ź 1����Q~Ջ���&�ˈ"_
��%�5��,7�nRn����.��     