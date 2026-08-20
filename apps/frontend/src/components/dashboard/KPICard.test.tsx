import { render, screen } from '@testing-library/react';
import { KPICard } from '@/components/dashboard/KPICard';
import { CreditCard, TrendingUp } from 'lucide-react';

describe('KPICard', () => {
  it('renders title and value correctly', () => {
    render(
      <KPICard
        title="Total Receivables"
        value="₹1,25,000"
        icon={<CreditCard className="h-6 w-6" />}
      />
    );

    expect(screen.getByText('Total Receivables')).toBeInTheDocument();
    expect(screen.getByText('₹1,25,000')).toBeInTheDocument();
  });

  it('renders change with increase type', () => {
    render(
      <KPICard
        title="Collected This Month"
        value="₹45,000"
        change="+23.1%"
        changeType="increase"
        icon={<TrendingUp className="h-6 w-6" />}
      />
    );

    expect(screen.getByText('+23.1%')).toBeInTheDocument();
    const changeElement = screen.getByText('+23.1%').closest('span');
    expect(changeElement).toHaveClass('text-green-600');
  });

  it('renders change with decrease type', () => {
    render(<KPICard title="Overdue Amount" value="₹12,000" change="-8.2%" changeType="decrease" />);

    expect(screen.getByText('-8.2%')).toBeInTheDocument();
    const changeElement = screen.getByText('-8.2%').closest('span');
    expect(changeElement).toHaveClass('text-red-600');
  });

  it('renders skeleton when loading', () => {
    render(<KPICard title="Total Receivables" value="₹0" loading />);

    expect(screen.getByText('Total Receivables')).toBeInTheDocument();
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('renders without icon when not provided', () => {
    render(<KPICard title="Pending Invoices" value="5" />);

    expect(screen.getByText('Pending Invoices')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});
