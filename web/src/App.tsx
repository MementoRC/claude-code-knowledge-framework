import React from 'react';
import { Routes, Route, Link as RouterLink } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Container,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import BarChartIcon from '@mui/icons-material/BarChart';
import GroupIcon from '@mui/icons-material/Group';
import PersonIcon from '@mui/icons-material/Person';
import HomeIcon from '@mui/icons-material/Home';

// Import theme and components
import { theme } from './theme/theme';
import PatternSearch from './components/PatternSearch/PatternSearch';
import PatternSubmission from './components/PatternSubmission/PatternSubmission';

// Placeholder Pages
const HomePage = () => (
  <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
    <Typography variant="h4" gutterBottom>
      Welcome to UCKN Dashboard
    </Typography>
    <Typography variant="body1" sx={{ mb: 3 }}>
      Use the navigation on the left to explore patterns, contribute new knowledge, and manage your team.
    </Typography>
    <Typography variant="h6" gutterBottom>
      Quick Actions
    </Typography>
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      <Button
        variant="contained"
        startIcon={<SearchIcon />}
        component={RouterLink}
        to="/patterns"
      >
        Search Patterns
      </Button>
      <Button
        variant="outlined"
        startIcon={<AddCircleOutlineIcon />}
        component={RouterLink}
        to="/submit"
      >
        Contribute Pattern
      </Button>
      <Button
        variant="outlined"
        startIcon={<BarChartIcon />}
        component={RouterLink}
        to="/analytics"
      >
        View Analytics
      </Button>
    </Box>
  </Container>
);

const AnalyticsDashboardPage = () => (
  <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
    <Typography variant="h4" gutterBottom>
      Analytics & Reporting
    </Typography>
    <Typography variant="body1">
      Insights into pattern usage, contribution trends, and system performance will be displayed here.
    </Typography>
  </Container>
);

const TeamManagementPage = () => (
  <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
    <Typography variant="h4" gutterBottom>
      Team Management
    </Typography>
    <Typography variant="body1">
      Manage teams, roles, and permissions within UCKN.
    </Typography>
  </Container>
);

const UserProfilePage = () => (
  <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
    <Typography variant="h4" gutterBottom>
      User Profile
    </Typography>
    <Typography variant="body1">
      View and edit your user profile and settings.
    </Typography>
  </Container>
);

const drawerWidth = 240;

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        <AppBar
          position="fixed"
          sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
        >
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              UCKN Dashboard
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Button color="inherit" component={RouterLink} to="/login">
              Login
            </Button>
          </Toolbar>
        </AppBar>
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar /> {/* Spacer for AppBar */}
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/">
                  <ListItemIcon>
                    <HomeIcon />
                  </ListItemIcon>
                  <ListItemText primary="Home" />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/patterns">
                  <ListItemIcon>
                    <SearchIcon />
                  </ListItemIcon>
                  <ListItemText primary="Pattern Search" />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/submit">
                  <ListItemIcon>
                    <AddCircleOutlineIcon />
                  </ListItemIcon>
                  <ListItemText primary="Contribute Pattern" />
                </ListItemButton>
              </ListItem>
            </List>
            <Divider />
            <List>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/analytics">
                  <ListItemIcon>
                    <BarChartIcon />
                  </ListItemIcon>
                  <ListItemText primary="Analytics" />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/teams">
                  <ListItemIcon>
                    <GroupIcon />
                  </ListItemIcon>
                  <ListItemText primary="Team Management" />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton component={RouterLink} to="/profile">
                  <ListItemIcon>
                    <PersonIcon />
                  </ListItemIcon>
                  <ListItemText primary="User Profile" />
                </ListItemButton>
              </ListItem>
            </List>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3, width: `calc(100% - ${drawerWidth}px)` }}>
          <Toolbar /> {/* Spacer for AppBar */}
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/patterns" element={<PatternSearch />} />
            <Route path="/submit" element={<PatternSubmission />} />
            <Route path="/analytics" element={<AnalyticsDashboardPage />} />
            <Route path="/teams" element={<TeamManagementPage />} />
            <Route path="/profile" element={<UserProfilePage />} />
            <Route path="/login" element={
              <Container maxWidth="sm" sx={{ mt: 8 }}>
                <Typography variant="h4" align="center" gutterBottom>
                  Login
                </Typography>
                <Typography variant="body1" align="center" color="text.secondary">
                  Authentication will be implemented in a future version.
                </Typography>
              </Container>
            } />
          </Routes>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;