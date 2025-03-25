import React from 'react';
import { Formik, Form } from 'formik';
import * as Yup from 'yup';
import { TextField, Button, MenuItem, Paper, Box } from '@mui/material';

const validationSchema = Yup.object({
  amount: Yup.number()
    .required('Amount is required')
    .positive('Amount must be positive'),
  category: Yup.string()
    .required('Category is required'),
  description: Yup.string()
    .required('Description is required')
});

const ExpenseForm = ({ onSubmit }) => {
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Formik
        initialValues={{
          amount: '',
          category: '',
          description: '',
          type: 'expense'
        }}
        validationSchema={validationSchema}
        onSubmit={onSubmit}
      >
        {({ values, handleChange, errors, touched }) => (
          <Form>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                name="amount"
                label="Amount"
                type="number"
                value={values.amount}
                onChange={handleChange}
                error={touched.amount && Boolean(errors.amount)}
                helperText={touched.amount && errors.amount}
              />
              <TextField
                name="category"
                select
                label="Category"
                value={values.category}
                onChange={handleChange}
                error={touched.category && Boolean(errors.category)}
                helperText={touched.category && errors.category}
              >
                <MenuItem value="groceries">Groceries</MenuItem>
                <MenuItem value="utilities">Utilities</MenuItem>
                <MenuItem value="entertainment">Entertainment</MenuItem>
                <MenuItem value="transport">Transport</MenuItem>
              </TextField>
              <TextField
                name="description"
                label="Description"
                multiline
                rows={2}
                value={values.description}
                onChange={handleChange}
                error={touched.description && Boolean(errors.description)}
                helperText={touched.description && errors.description}
              />
              <Button variant="contained" type="submit" color="primary">
                Add Expense
              </Button>
            </Box>
          </Form>
        )}
      </Formik>
    </Paper>
  );
};

export default ExpenseForm;
