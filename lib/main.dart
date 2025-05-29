import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:campoundnew/auth/AuthCubitadmin.dart';
import 'package:campoundnew/pages/login_screen.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() {
  final dio = Dio();
  runApp(CampoundApp(dio: dio));
}

class CampoundApp extends StatelessWidget {
  final Dio dio;

  const CampoundApp({super.key, required this.dio});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthCubit>(
          create: (context) => AuthCubit(dio),
        ),
        BlocProvider<Authcubitadmin>(
          create: (context) =>
              Authcubitadmin(dio), // إضافة BlocProvider للمسؤولين
        ),
        // يمكنك إضافة المزيد من BlocProviders إذا لزم الأمر
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false, // إخفاء شريط Debug

        title: 'Campound App',
        theme: ThemeData(
          primarySwatch: Colors.blue,
        ),
        home: const LoginScreen(),
      ),
    );
  }
}
