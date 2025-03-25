import React, { useState, useEffect } from 'react';
import { Grid, Container } from '@mui/material';
import ExpenseChart from '../components/ExpenseChart';
import NewsSection from '../components/NewsSection';
import PredictionChart from '../components/PredictionChart';
import ExpenseForm from '../components/ExpenseForm';
import { fetchExpenses, addExpense } from '../api/expenses';
import { fetchNews } from '../api/news';
import { fetchPredictions } from '../api/predictions';

const Dashboard = () => {
  const [expenses, setExpenses] = useState([]);
  const [news, setNews] = useState([]);
  const [predictions, setPredictions] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const [expenseData, newsData, predictionData] = await Promise.all([
        fetchExpenses(),
        fetchNews(),
        fetchPredictions()
      ]);
      
      setExpenses(expenseData);
      setNews(newsData);
      setPredictions(predictionData);
    };
    
    loadData();
  }, []);

  const handleExpenseSubmit = async (values, { resetForm }) => {
    await addExpense(values);
    const newExpenses = await fetchExpenses();
    setExpenses(newExpenses);
    resetForm();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <ExpenseChart data={expenses} />
        </Grid>
        <Grid item xs={12} md={4}>
          <ExpenseForm onSubmit={handleExpenseSubmit} />
        </Grid>
        <Grid item xs={12}>
          <PredictionChart data={predictions} />
        </Grid>
        <Grid item xs={12}>
          <NewsSection news={news} />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
