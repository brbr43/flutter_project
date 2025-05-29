import 'package:flutter/material.dart';

// ignore: must_be_immutable
class LoiginWidgate extends StatelessWidget {
  String? text1;
  Function(String)? onChanged;
  bool? obscur;

  LoiginWidgate(
      {Key? key,
      this.onChanged,
      this.text1,
      this.obscur = false,
      required TextEditingController controller})
      : super(key: key);
  @override
  Widget build(BuildContext context) {
    return TextFormField(
      obscureText: obscur!,
      validator: (data) {
        if (data!.isEmpty) {
          return 'Please enter the field';
        }
        return null;
      },
      onChanged: onChanged,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
          label: Text(
            '$text1',
            style: const TextStyle(color: Colors.white),
          ),
          focusedBorder: const OutlineInputBorder(
            borderSide: BorderSide(color: Colors.white),
          ),
          enabledBorder: const OutlineInputBorder(
              borderSide: BorderSide(color: Colors.white))),
    );
  }
}
