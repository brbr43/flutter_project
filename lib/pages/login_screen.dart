import 'package:campoundnew/admin_pages/home_screen_admin.dart';
import 'package:campoundnew/auth/AuthCubitadmin.dart' as adminAuth;
import 'package:campoundnew/pages/home_screen.dart';

import 'package:campoundnew/pages/signup_screen.dart';
import 'package:campoundnew/widget/custom_textfield.dart';
import 'package:campoundnew/widget/login_widgate.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../auth/AuthCubit.dart' as userAuth;

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  String? email;
  String? password;
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  GlobalKey<FormState> formKey = GlobalKey();
  bool loadingState = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color.fromARGB(255, 47, 7, 226),
      body: Form(
        key: formKey,
        child: ListView(
          children: [
            const SizedBox(height: 75),
            CircleAvatar(
              radius: 100,
              backgroundColor: Colors.white,
              child: CircleAvatar(
                radius: 90,
                backgroundImage: AssetImage('assets/images/camp.jpg'),
              ),
            ),
            const SizedBox(height: 10),
            const Center(
              child: Text(
                'Welcome to our compound',
                style: TextStyle(
                    color: Color.fromARGB(255, 248, 248, 249),
                    fontSize: 26,
                    fontFamily: 'Pacifico'),
              ),
            ),
            const SizedBox(height: 75),
            const Row(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                Padding(
                  padding: EdgeInsets.all(9.0),
                  child: Text(
                    'Login',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                    ),
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: LoiginWidgate(
                controller: _emailController,
                onChanged: (data) {
                  email = data;
                },
                text1: 'Email',
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: LoiginWidgate(
                controller: _passwordController,
                obscur: true,
                onChanged: (data) {
                  password = data;
                },
                text1: 'Password',
              ),
            ),
            CustomTextfield(
              onTab: () {
                if (formKey.currentState!.validate()) {
                  // Using AuthCubit to log in
                  if (email!.contains('admin')) {
                    context
                        .read<adminAuth.Authcubitadmin>()
                        .login(email!, password!);
                  } else {
                    context.read<userAuth.AuthCubit>().login(email!, password!);
                  }
                }
              },
              text2: 'Log in',
              onChanged: (data) {},
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Don’t have any account?',
                  style: TextStyle(color: Colors.white),
                ),
                GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => SignupScreen(),
                      ),
                    );
                  },
                  child: const Text(
                    ' Sign Up',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),

            // BlocListener for normal user
            BlocListener<userAuth.AuthCubit, userAuth.AuthState>(
              listener: (context, state) {
                if (state is userAuth.AuthLoading) {
                  setState(() {
                    loadingState = true;
                  });
                } else if (state is userAuth.AuthSuccess) {
                  setState(() {
                    loadingState = false;
                  });
                  showSnackbar(context, state.message, Colors.green);
                  // Navigate to HomeScreen if user is normal
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => HomeScreen()),
                  );
                } else if (state is userAuth.AuthError) {
                  setState(() {
                    loadingState = false;
                  });
                  showSnackbar(context, state.message, Colors.red);
                }
              },
              child: Container(),
            ),

            // BlocListener for admin
            BlocListener<adminAuth.Authcubitadmin, adminAuth.AuthState>(
              listener: (context, state) {
                if (state is adminAuth.AuthLoading) {
                  setState(() {
                    loadingState = true;
                  });
                } else if (state is adminAuth.AuthSuccess) {
                  setState(() {
                    loadingState = false;
                  });
                  showSnackbar(context, state.message, Colors.green);
                  // Navigate to HomeScreenAdmin if user is admin
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => HomeScreenAdmin()),
                  );
                } else if (state is adminAuth.AuthError) {
                  setState(() {
                    loadingState = false;
                  });
                  showSnackbar(context, state.message, Colors.red);
                }
              },
              child: Container(),
            ),
          ],
        ),
      ),
    );
  }

  void showSnackbar(BuildContext context, String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
      ),
    );
  }
}
